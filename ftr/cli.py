# ftr/cli.py
from __future__ import annotations
import argparse, csv, os, os.path
from typing import List, Tuple

from .grid import GridWorld
from .planners import repeated_forward, repeated_backward, adaptive_astar, RunStats
from .viz import draw_world_png

def format_stats(name: str, s: RunStats) -> str:
    return (f"{name:20s} | reached={s.reached!s:5s} | moves={s.moves:4d} | "
            f"replans={s.replans:3d} | expansions={s.expansions:6d} | "
            f"time={s.elapsed_sec*1000:7.1f} ms")

def run_all_algs(world: GridWorld, out_dir: str | None = None, base_tag: str = "run") -> List[Tuple[str, RunStats]]:
    results: List[Tuple[str, RunStats]] = []

    s1 = repeated_forward(world, tie_break="larger_g")
    results.append(("forward_largerg", s1))
    if out_dir:
        draw_world_png(world, s1.path_taken, s1.expanded_all, os.path.join(out_dir, f"{base_tag}_forward_largerg.png"))

    s2 = repeated_forward(world, tie_break="smaller_g")
    results.append(("forward_smallerg", s2))
    if out_dir:
        draw_world_png(world, s2.path_taken, s2.expanded_all, os.path.join(out_dir, f"{base_tag}_forward_smallerg.png"))

    s3 = repeated_backward(world, tie_break="larger_g")
    results.append(("backward", s3))
    if out_dir:
        draw_world_png(world, s3.path_taken, s3.expanded_all, os.path.join(out_dir, f"{base_tag}_backward.png"))

    s4 = adaptive_astar(world, tie_break="larger_g")
    results.append(("adaptive", s4))
    if out_dir:
        draw_world_png(world, s4.path_taken, s4.expanded_all, os.path.join(out_dir, f"{base_tag}_adaptive.png"))

    return results

# -------- subcommands --------

def cmd_gen(args: argparse.Namespace) -> None:
    os.makedirs(args.out, exist_ok=True)
    for i in range(args.count):
        gw = GridWorld.random(n=args.size, p_blocked=args.p, seed=(args.seed + i) if args.seed is not None else None)
        path = os.path.join(args.out, f"grid_{i:03d}.txt")
        gw.save(path)
        print("wrote", path)

def cmd_demo(args: argparse.Namespace) -> None:
    gw = GridWorld.load(args.env)
    os.makedirs(args.out, exist_ok=True)
    results = run_all_algs(gw, out_dir=args.out, base_tag=os.path.splitext(os.path.basename(args.env))[0])
    for name, st in results:
        print(format_stats(name, st))

def cmd_bench(args: argparse.Namespace) -> None:
    envs = sorted(p for p in os.listdir(args.envdir) if p.endswith(".txt"))
    os.makedirs(args.out, exist_ok=True)
    rows = []
    for fname in envs:
        fpath = os.path.join(args.envdir, fname)
        gw = GridWorld.load(fpath)
        base = os.path.splitext(fname)[0]
        results = run_all_algs(gw, out_dir=args.out, base_tag=base)
        for name, st in results:
            print(f"{fname} :: {format_stats(name, st)}")
            rows.append({
                "env": fname,
                "alg": name,
                "reached": st.reached,
                "moves": st.moves,
                "replans": st.replans,
                "expansions": st.expansions,
                "time_sec": round(st.elapsed_sec, 6),
            })
    if args.csv:
        with open(args.csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print("wrote CSV:", args.csv)

def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Fast Trajectory Replanning (A* variants)")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gen", help="generate random grids")
    g.add_argument("--count", type=int, default=30)
    g.add_argument("--size", type=int, default=51)
    g.add_argument("--p", type=float, default=0.30)
    g.add_argument("--out", type=str, default="envs")
    g.add_argument("--seed", type=int, default=None)
    g.set_defaults(func=cmd_gen)

    d = sub.add_parser("demo", help="run all algorithms on one env and save PNGs")
    d.add_argument("--env", type=str, required=True)
    d.add_argument("--out", type=str, default="runs")
    d.set_defaults(func=cmd_demo)

    b = sub.add_parser("bench", help="run all algorithms on every .txt in a folder")
    b.add_argument("--envdir", type=str, required=True)
    b.add_argument("--out", type=str, default="runs")
    b.add_argument("--csv", type=str, default="")
    b.set_defaults(func=cmd_bench)

    return p

def main():
    ap = build_argparser()
    args = ap.parse_args()
    args.func(args)
