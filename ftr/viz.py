# ftr/viz.py
from __future__ import annotations
import os
from typing import List, Optional, Set
try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

from .types import Coord
from .grid import GridWorld

def draw_world_png(world: GridWorld,
                   path: Optional[List[Coord]],
                   expanded: Optional[Set[Coord]],
                   out_png: str,
                   cell: int = 10) -> None:
    if not PIL_AVAILABLE:
        print("Pillow not installed; skipping PNG:", out_png)
        return

    n = world.n
    W = n * cell
    img = Image.new("RGB", (W, W), (255, 255, 255))
    drw = ImageDraw.Draw(img)

    # base grid
    for r in range(n):
        for c in range(n):
            x0, y0 = c * cell, r * cell
            x1, y1 = x0 + cell, y0 + cell
            if world.blocked[r][c]:
                drw.rectangle((x0, y0, x1, y1), fill=(0, 0, 0))
            else:
                drw.rectangle((x0, y0, x1, y1), fill=(240, 240, 240))

    # expanded cells
    if expanded:
        for (r, c) in expanded:
            x0, y0 = c * cell, r * cell
            x1, y1 = x0 + cell, y0 + cell
            drw.rectangle((x0, y0, x1, y1), fill=(255, 200, 200))

    # path
    if path and len(path) > 1:
        for (r, c) in path:
            x0, y0 = c * cell, r * cell
            x1, y1 = x0 + cell, y0 + cell
            drw.rectangle((x0, y0, x1, y1), fill=(160, 190, 255))

    # start/goal
    sr, sc = world.start
    gr, gc = world.goal
    drw.rectangle((sc*cell, sr*cell, sc*cell+cell, sr*cell+cell), fill=(100, 220, 120))
    drw.rectangle((gc*cell, gr*cell, gc*cell+cell, gr*cell+cell), fill=(255, 170, 80))

    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    img.save(out_png)
