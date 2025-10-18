# ftr/grid.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import random, os
from .types import Coord

@dataclass
class GridWorld:
    n: int
    blocked: List[List[bool]]  # True=blocked
    start: Coord
    goal: Coord

    @staticmethod
    def random(n: int = 51, p_blocked: float = 0.30, seed: Optional[int] = None) -> "GridWorld":
        if seed is not None:
            random.seed(seed)
        blocked = [[random.random() < p_blocked for _ in range(n)] for _ in range(n)]
        start, goal = (0, 0), (n - 1, n - 1)
        blocked[start[0]][start[1]] = False
        blocked[goal[0]][goal[1]] = False
        return GridWorld(n, blocked, start, goal)

    @staticmethod
    def load(path: str) -> "GridWorld":
        with open(path, "r") as f:
            lines = [line.strip() for line in f if line.strip()]

        header = lines[0].split()
        if header and header[0] == "GRID" and len(header) == 6:
            n = int(header[1])
            sr, sc, gr, gc = map(int, header[2:])
            arr = [[c == "1" for c in lines[i + 1]] for i in range(n)]
            return GridWorld(n, arr, (sr, sc), (gr, gc))

        # fallback (legacy flat format: lines of 0/1; start=(0,0), goal=(n-1,n-1))
        arr = [[c == "1" for c in row] for row in lines]
        n = len(arr)
        return GridWorld(n, arr, (0, 0), (n - 1, n - 1))

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(f"GRID {self.n} {self.start[0]} {self.start[1]} {self.goal[0]} {self.goal[1]}\n")
            for r in range(self.n):
                f.write("".join("1" if self.blocked[r][c] else "0" for c in range(self.n)) + "\n")

    def in_bounds(self, s: Coord) -> bool:
        r, c = s
        return 0 <= r < self.n and 0 <= c < self.n

    def is_blocked(self, s: Coord) -> bool:
        r, c = s
        return self.blocked[r][c]

    def neighbors(self, s: Coord):
        r, c = s
        cand = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
        return [p for p in cand if self.in_bounds(p)]
