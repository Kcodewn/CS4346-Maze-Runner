# ftr/knowledge.py
from __future__ import annotations
from typing import Set
from .types import Coord
from .grid import GridWorld

class Knowledge:
    """
    Agent's knowledge:
    - Treat UNKNOWN cells as traversable when planning
    - Only forbid cells known to be blocked
    """
    def __init__(self, n: int):
        self.n = n
        self.known_blocked: Set[Coord] = set()
        self.known_unblocked: Set[Coord] = set()

    def is_known_blocked(self, s: Coord) -> bool:
        return s in self.known_blocked

    def mark(self, s: Coord, blocked: bool) -> None:
        if blocked:
            self.known_blocked.add(s)
            self.known_unblocked.discard(s)
        else:
            self.known_unblocked.add(s)
            self.known_blocked.discard(s)

    def sense_neighbors(self, world: GridWorld, at: Coord) -> None:
        for nb in world.neighbors(at):
            self.mark(nb, blocked=world.is_blocked(nb))

    def traversable_for_planning(self, s: Coord) -> bool:
        return not self.is_known_blocked(s)
