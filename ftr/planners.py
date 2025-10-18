# ftr/planners.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
import time

from .types import Coord
from .grid import GridWorld
from .knowledge import Knowledge
from .astar import astar_once
from .heuristics import manhattan  # used for initializing adaptive table

@dataclass
class RunStats:
    reached: bool
    moves: int
    replans: int
    expansions: int
    elapsed_sec: float
    path_taken: List[Coord]
    expanded_all: Set[Coord]

def _init(kb: Knowledge, world: GridWorld) -> None:
    kb.mark(world.start, False)
    kb.mark(world.goal, False)
    kb.sense_neighbors(world, world.start)

def repeated_forward(world: GridWorld, tie_break: str = "larger_g") -> RunStats:
    kb = Knowledge(world.n)
    _init(kb, world)
    cur = world.start

    expansions_total = 0
    replans = 0
    path_taken: List[Coord] = [cur]
    expanded_all: Set[Coord] = set()
    t0 = time.perf_counter()

    while cur != world.goal:
        res = astar_once(cur, world.goal, world, kb, tie_break=tie_break)
        replans += 1
        expansions_total += len(res.expanded)
        expanded_all |= res.expanded

        if res.path is None:
            return RunStats(False, len(path_taken) - 1, replans, expansions_total, time.perf_counter() - t0, path_taken, expanded_all)

        for step in res.path[1:]:
            if world.is_blocked(step):
                kb.mark(step, True)
                kb.sense_neighbors(world, cur)
                break
            cur = step
            path_taken.append(cur)
            kb.mark(cur, False)
            kb.sense_neighbors(world, cur)
            if cur == world.goal:
                break

    return RunStats(True, len(path_taken) - 1, replans, expansions_total, time.perf_counter() - t0, path_taken, expanded_all)

def repeated_backward(world: GridWorld, tie_break: str = "larger_g") -> RunStats:
    kb = Knowledge(world.n)
    _init(kb, world)
    cur = world.start

    expansions_total = 0
    replans = 0
    path_taken: List[Coord] = [cur]
    expanded_all: Set[Coord] = set()
    t0 = time.perf_counter()

    while cur != world.goal:
        res = astar_once(world.goal, cur, world, kb, tie_break=tie_break)
        replans += 1
        expansions_total += len(res.expanded)
        expanded_all |= res.expanded

        if res.path is None:
            return RunStats(False, len(path_taken) - 1, replans, expansions_total, time.perf_counter() - t0, path_taken, expanded_all)

        fwd_path = list(reversed(res.path))
        for step in fwd_path[1:]:
            if world.is_blocked(step):
                kb.mark(step, True)
                kb.sense_neighbors(world, cur)
                break
            cur = step
            path_taken.append(cur)
            kb.mark(cur, False)
            kb.sense_neighbors(world, cur)
            if cur == world.goal:
                break

    return RunStats(True, len(path_taken) - 1, replans, expansions_total, time.perf_counter() - t0, path_taken, expanded_all)

def adaptive_astar(world: GridWorld, tie_break: str = "larger_g") -> RunStats:
    kb = Knowledge(world.n)
    _init(kb, world)
    cur = world.start

    # prefill Manhattan
    h_table = [[manhattan((r, c), world.goal) for c in range(world.n)] for r in range(world.n)]

    expansions_total = 0
    replans = 0
    path_taken: List[Coord] = [cur]
    expanded_all: Set[Coord] = set()
    t0 = time.perf_counter()

    while cur != world.goal:
        res = astar_once(cur, world.goal, world, kb, tie_break=tie_break, h_table=h_table)
        replans += 1
        expansions_total += len(res.expanded)
        expanded_all |= res.expanded

        if res.path is None:
            return RunStats(False, len(path_taken) - 1, replans, expansions_total, time.perf_counter() - t0, path_taken, expanded_all)

        # Adaptive update if we saw a goal g-value
        if world.goal in res.gvals:
            g_goal = res.gvals[world.goal]
            for s in res.expanded:
                if s in res.gvals:
                    r, c = s
                    h_table[r][c] = g_goal - res.gvals[s]

        for step in res.path[1:]:
            if world.is_blocked(step):
                kb.mark(step, True)
                kb.sense_neighbors(world, cur)
                break
            cur = step
            path_taken.append(cur)
            kb.mark(cur, False)
            kb.sense_neighbors(world, cur)
            if cur == world.goal:
                break

    return RunStats(True, len(path_taken) - 1, replans, expansions_total, time.perf_counter() - t0, path_taken, expanded_all)
