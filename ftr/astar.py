# ftr/astar.py
from __future__ import annotations
from typing import Dict, List, Optional, Set, Tuple
import heapq
from .types import Coord
from .grid import GridWorld
from .knowledge import Knowledge
from .heuristics import manhattan

class AStarResult:
    def __init__(self, path: Optional[List[Coord]], expanded: Set[Coord], gvals: Dict[Coord, int]):
        self.path = path
        self.expanded = expanded
        self.gvals = gvals

def astar_once(
    start: Coord,
    goal: Coord,
    world: GridWorld,
    kb: Knowledge,
    tie_break: str = "larger_g",          # or "smaller_g"
    h_table: Optional[List[List[int]]] = None,
) -> AStarResult:
    """
    A* over the agent's current knowledge.
    Unknown cells are assumed free; known-blocked are forbidden.
    """

    def h(s: Coord) -> int:
        if h_table is not None:
            return h_table[s[0]][s[1]]
        return manhattan(s, goal)

    openh: List[Tuple[int, int, int, Coord]] = []
    g: Dict[Coord, int] = {start: 0}
    parent: Dict[Coord, Coord] = {}
    closed: Set[Coord] = set()
    counter = 0

    f0 = g[start] + h(start)
    gkey = -g[start] if tie_break == "larger_g" else g[start]
    heapq.heappush(openh, (f0, gkey, counter, start))
    counter += 1

    while openh:
        fcur, gk, _, s = heapq.heappop(openh)
        if s in closed:
            continue
        closed.add(s)

        if s == goal:
            # reconstruct
            path = [s]
            while s in parent:
                s = parent[s]
                path.append(s)
            path.reverse()
            return AStarResult(path, closed, g)

        for nb in world.neighbors(s):
            if not kb.traversable_for_planning(nb):
                continue
            tentative = g[s] + 1
            if nb not in g or tentative < g[nb]:
                g[nb] = tentative
                parent[nb] = s
                ff = tentative + h(nb)
                g_term = -tentative if tie_break == "larger_g" else tentative
                heapq.heappush(openh, (ff, g_term, counter, nb))
                counter += 1

    return AStarResult(None, closed, g)
