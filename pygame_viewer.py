# ftr/pygame_viewer.py (fullscreen + fog-of-war)
from __future__ import annotations
import argparse
from dataclasses import dataclass
from typing import List, Set, Tuple
import os
import pygame

from .grid import GridWorld
from .knowledge import Knowledge
from .astar import astar_once

Coord = Tuple[int, int]  # (row, col)

@dataclass
class Colors:
    BG = (18, 18, 22)
    WALL = (35, 35, 44)
    FLOOR = (230, 230, 240)
    PLAYER = (220, 90, 90)
    GOAL = (90, 160, 220)
    PATH = (70, 170, 110)
    EXPANDED = (160, 200, 160)
    GRID = (60, 60, 70)

def _is_cmd_ctrl_f(event):
    mods = event.mod
    KMOD_CMD = getattr(pygame, "KMOD_META", 0) | getattr(pygame, "KMOD_GUI", 0)
    return event.key == pygame.K_f and (mods & pygame.KMOD_CTRL) and (mods & KMOD_CMD)

class Viewer:
    def __init__(self, world: GridWorld, cell_size: int = 28, fps: int = 60,
                 vision_radius: int = 6, fullscreen: bool = False, speed: float = 6.0,
                 env_dir: str | None = None):
        self.world = world
        self.cell = cell_size
        self.fps = fps
        self.vision_radius = vision_radius
        self.speed_tiles_per_sec = speed
        self.env_dir = env_dir
        self.env_files: List[str] = []
        self.env_index = -1

        self.tie_break_strategy = "larger_g"
        self.cur: Coord = world.start
        self.goal: Coord = world.goal
        self.kb = Knowledge(world.n)
        self.kb.sense_neighbors(world, self.cur)

        self.seen: Set[Coord] = set()
        self.visible: Set[Coord] = set()

        self.autopilot = False
        self._step_timer = 0.0

        self.manual_speed_tiles_per_sec = 20.0 # Movement speed in manual mode
        self._manual_move_timer = 0.0
        self._manual_move_interval = 1.0 / self.manual_speed_tiles_per_sec

        self.show_grid = False
        self.hard_alpha = 220    # unseen
        self.soft_alpha = 140    # seen but currently not visible

        self.fullscreen = fullscreen
        self._recreate_display()
        pygame.display.set_caption("Maze Runner + Fog of War")
        self.clock = pygame.time.Clock()

        # initial fog
        self._reset_state()
        self._update_fog()

        if self.env_dir:
            self._find_env_files()

    # ----------------- display / fullscreen -----------------
    def _recreate_display(self) -> None:
        W, H = self.world.n * self.cell, self.world.n * self.cell
        flags = pygame.SCALED | (pygame.FULLSCREEN if self.fullscreen else 0)
        self.screen = pygame.display.set_mode((W, H), flags)

    def toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        self._recreate_display()

    def _recalculate_step_interval(self) -> None:
        self._step_interval = 1.0 / self.speed_tiles_per_sec

    # ----------------- planning / fog -----------------
    def _reset_state(self) -> None:
        """Resets the agent's state for the current world."""
        self.cur = self.world.start
        self.goal = self.world.goal
        self.kb = Knowledge(self.world.n)
        self.kb.sense_neighbors(self.world, self.cur)
        self.seen: Set[Coord] = set()
        self.visible: Set[Coord] = set()
        self.path: List[Coord] = []
        self.path_index = 0
        self.expanded_last: Set[Coord] = set()
        self._recalculate_step_interval()
        self._update_fog()
        self._plan_from_current()

    def _find_env_files(self) -> None:
        if self.env_dir and os.path.isdir(self.env_dir):
            self.env_files = sorted([f for f in os.listdir(self.env_dir) if f.endswith(".txt")])

    def _load_env_by_index(self, index: int) -> None:
        if not self.env_files or not (0 <= index < len(self.env_files)):
            return
        self.env_index = index
        filepath = os.path.join(self.env_dir, self.env_files[self.env_index])
        print(f"Loading: {filepath}")
        self.world = GridWorld.load(filepath)
        self._reset_state()

    def _plan_from_current(self) -> None:
        res = astar_once(self.cur, self.goal, self.world, self.kb, tie_break=self.tie_break_strategy)
        self.expanded_last = res.expanded
        self.path = res.path or []
        self.path_index = 0

    def _update_fog(self) -> None:
        self.visible.clear()
        radius = self.vision_radius
        cr, cc = self.cur
        n = self.world.n
        self.visible = set()
        r2 = radius * radius
        rmin, rmax = max(0, cr - radius), min(n - 1, cr + radius)
        cmin, cmax = max(0, cc - radius), min(n - 1, cc + radius)
        for r in range(rmin, rmax + 1):
            for c in range(cmin, cmax + 1):
                if (r - cr) * (r - cr) + (c - cc) * (c - cc) <= r2:
                    if self._has_los((cr, cc), (r, c)):
                        self.visible.add((r, c))
                        self.seen.add((r, c))

    def _has_los(self, a: Coord, b: Coord) -> bool:
        (r0, c0), (r1, c1) = a, b
        dr = abs(r1 - r0)
        dc = abs(c1 - c0)
        sr = 1 if r0 < r1 else -1
        sc = 1 if c0 < c1 else -1
        err = dr - dc
        r, c = r0, c0
        first = True
        while True:
            if not first and (r, c) != b and self.world.is_blocked((r, c)):
                return False
            if r == r1 and c == c1:
                return True
            first = False
            e2 = 2 * err
            if e2 > -dc:
                err -= dc; r += sr
            if e2 < dr:
                err += dr; c += sc

    def _step_along_plan(self) -> None:
        if not self.path or self.path_index >= len(self.path):
            self._plan_from_current()
            return
        nxt = self.path[self.path_index]
        if self.world.is_blocked(nxt):
            self.kb.mark(nxt, True)
            self.kb.sense_neighbors(self.world, self.cur)
            self._plan_from_current()
            return
        self.cur = nxt
        self.path_index += 1
        self.kb.mark(self.cur, False)
        self.kb.sense_neighbors(self.world, self.cur)
        self._update_fog()

    # ----------------- draw -----------------
    def draw(self) -> None:
        n, cell = self.world.n, self.cell
        scr = self.screen
        scr.fill(Colors.BG)

        for r in range(n):
            for c in range(n):
                rect = pygame.Rect(c * cell, r * cell, cell, cell)
                color = Colors.WALL if self.world.blocked[r][c] else Colors.FLOOR
                scr.fill(color, rect)

        for (r, c) in self.path:
            x, y = c * cell + cell // 4, r * cell + cell // 4
            rect = pygame.Rect(x, y, cell // 2, cell // 2)
            pygame.draw.rect(scr, Colors.PATH, rect, border_radius=4)

        for (r, c) in self.expanded_last:
            rect = pygame.Rect(c * cell, r * cell, cell, cell)
            s = pygame.Surface((cell, cell), pygame.SRCALPHA)
            s.fill((*Colors.EXPANDED, 60))
            scr.blit(s, rect.topleft)

        gr, gc = self.goal
        goal_rect = pygame.Rect(gc * cell + 4, gr * cell + 4, cell - 8, cell - 8)
        pygame.draw.rect(scr, Colors.GOAL, goal_rect, border_radius=6)

        pr, pc = self.cur
        player_rect = pygame.Rect(pc * cell + 6, pr * cell + 6, cell - 12, cell - 12)
        pygame.draw.rect(scr, Colors.PLAYER, player_rect, border_radius=8)

        # Fog
        fog_surface = pygame.Surface((n * cell, n * cell), pygame.SRCALPHA)
        for r in range(n):
            for c in range(n):
                if self.world.blocked[r][c]:
                    continue
                if (r, c) not in self.seen:
                    fog_surface.fill((0, 0, 0, self.hard_alpha), pygame.Rect(c * cell, r * cell, cell, cell))
        for (r, c) in self.seen:
            if (r, c) not in self.visible:
                fog_surface.fill((0, 0, 0, self.soft_alpha), pygame.Rect(c * cell, r * cell, cell, cell))
        scr.blit(fog_surface, (0, 0))

        if self.show_grid:
            for i in range(n + 1):
                pygame.draw.line(scr, Colors.GRID, (i * cell, 0), (i * cell, n * cell))
                pygame.draw.line(scr, Colors.GRID, (0, i * cell), (n * cell, i * cell))

        pygame.display.flip()

    # ----------------- loop -----------------
    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(self.fps) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self.autopilot = not self.autopilot
                    elif event.key == pygame.K_r:
                        self._reset_state()
                    elif event.key == pygame.K_g:
                        self.world = GridWorld.random(n=self.world.n, p_blocked=0.30)
                        self._reset_state()
                    elif event.key == pygame.K_LEFTBRACKET and self.env_files: # Previous maze '['
                        new_index = (self.env_index - 1 + len(self.env_files)) % len(self.env_files)
                        self._load_env_by_index(new_index)
                    elif event.key == pygame.K_RIGHTBRACKET and self.env_files: # Next maze ']'
                        new_index = (self.env_index + 1) % len(self.env_files)
                        self._load_env_by_index(new_index)
                    elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                        self.vision_radius = min(self.vision_radius + 1, 99)
                        self._update_fog()
                    elif event.key == pygame.K_MINUS:
                        self.vision_radius = max(self.vision_radius - 1, 1)
                        self._update_fog()
                    elif event.key == pygame.K_PAGEUP:
                        self.speed_tiles_per_sec = min(self.speed_tiles_per_sec + 1, 60)
                        self._recalculate_step_interval()
                    elif event.key == pygame.K_PAGEDOWN:
                        self.speed_tiles_per_sec = max(self.speed_tiles_per_sec - 1, 1)
                        self._recalculate_step_interval()
                    elif event.key == pygame.K_h:
                        self.show_grid = not self.show_grid
                    elif (event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT)) or _is_cmd_ctrl_f(event):
                        self.toggle_fullscreen()
                    elif event.key == pygame.K_F11:
                        self.toggle_fullscreen()
                    elif event.key == pygame.K_t:
                        self.tie_break_strategy = "smaller_g" if self.tie_break_strategy == "larger_g" else "larger_g"
                        print(f"Tie-breaking strategy set to: {self.tie_break_strategy}")
                        self._plan_from_current()

            self._manual_move_timer += dt

            keys = pygame.key.get_pressed()
            dr = dc = 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dc = -1
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dc = 1
            elif keys[pygame.K_UP] or keys[pygame.K_w]:
                dr = -1
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dr = 1

            if dr != 0 or dc != 0:
                # If a move key is pressed and the move timer is ready
                if self._manual_move_timer >= self._manual_move_interval:
                    nr, nc = self.cur[0] + dr, self.cur[1] + dc
                    if self.world.in_bounds((nr, nc)) and not self.world.is_blocked((nr, nc)):
                        self.cur = (nr, nc)
                        self.kb.mark(self.cur, False)
                        self.kb.sense_neighbors(self.world, self.cur)
                        self._update_fog()
                        self._plan_from_current() # Always replan after a manual move
                        self._manual_move_timer = 0 # Reset timer after move

            if self.autopilot and self.cur != self.goal:
                self._step_timer += dt
                while self._step_timer >= self._step_interval and self.cur != self.goal:
                    self._step_along_plan()
                    self._step_timer -= self._step_interval

            self.draw()

def main():
    parser = argparse.ArgumentParser(description="Maze Runner viewer with fog-of-war")
    parser.add_argument("--n", type=int, default=31, help="Grid size when generating random maps")
    parser.add_argument("--p", type=float, default=0.30, help="Block probability for random maps")
    parser.add_argument("--load", type=str, default=None, help="Load a saved world (.txt)")
    parser.add_argument("--cell", type=int, default=28, help="Cell size in pixels")
    parser.add_argument("--envdir", type=str, default="envs", help="Directory of envs to cycle through with [ and ]")
    parser.add_argument("--fps", type=int, default=60, help="Frames per second")
    parser.add_argument("--vision", type=int, default=6, help="Vision radius in tiles")
    parser.add_argument("--speed", type=float, default=6.0, help="Autopilot speed in tiles/sec")
    parser.add_argument("--fullscreen", action="store_true", help="Start in fullscreen (toggle Option+Enter / F11)")
    args = parser.parse_args()

    # Determine initial world
    if args.load:
        world = GridWorld.load(args.load)
    elif os.path.isdir(args.envdir) and any(f.endswith(".txt") for f in os.listdir(args.envdir)):
        first_env = sorted([f for f in os.listdir(args.envdir) if f.endswith(".txt")])[0]
        world = GridWorld.load(os.path.join(args.envdir, first_env))
    else:
        world = GridWorld.random(n=args.n, p_blocked=args.p)

    pygame.init()
    try:
        Viewer(world, cell_size=args.cell, fps=args.fps, vision_radius=args.vision, fullscreen=args.fullscreen, speed=args.speed, env_dir=args.envdir).run()
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()