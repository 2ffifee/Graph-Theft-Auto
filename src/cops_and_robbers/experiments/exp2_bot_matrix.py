"""Experiment 2 — Bot vs Bot matrix (slide 15).

For each pair (cop strategy, robber strategy) in the chosen set, plays N games
on freshly generated graphs and reports the cop win-rate.

Default configuration:
  four graph buckets (n=12/30, sparse/dense), T=20/50, 1 cop,
  N=100 games per cell, graph_type=any, heuristic placement.

Usage::

    python -m cops_and_robbers.experiments.exp2_bot_matrix
    python -m cops_and_robbers.experiments.exp2_bot_matrix --games 200
    python -m cops_and_robbers.experiments.exp2_bot_matrix --no-minimax  # skip slow cells
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from cops_and_robbers.experiments.runner import (
    BotSpec, simulate_batch, write_csv,
)

DEFAULT_OUTPUT_DIR = "results"
DEFAULT_BUCKETS = [
    ("n12_sparse", 12, 18),
    ("n12_dense", 12, 30),
    ("n30_sparse", 30, 45),
    ("n30_dense", 30, 75),
]


def build_strategy_set(include_minimax: bool, minimax_depth: int) -> list[BotSpec]:
    specs = [BotSpec("random"), BotSpec("greedy")]
    if include_minimax:
        specs.append(BotSpec("minimax", depth=minimax_depth))
    return specs


def selected_buckets(args: argparse.Namespace) -> list[tuple[str, int, int]]:
    if args.n is not None or args.m is not None:
        n = args.n if args.n is not None else 12
        m = args.m if args.m is not None else round(1.5 * n)
        return [(f"custom_n{n}_m{m}", n, m)]
    wanted = set(args.buckets)
    return [bucket for bucket in DEFAULT_BUCKETS if bucket[0] in wanted]


def round_limit_for_bucket(n: int, args: argparse.Namespace) -> int:
    if args.T is not None:
        return args.T
    return max(args.t_min, int(round(args.t_per_n * n)))


def run(args: argparse.Namespace) -> None:
    strategies = build_strategy_set(
        include_minimax=not args.no_minimax,
        minimax_depth=args.minimax_depth,
    )
    buckets = selected_buckets(args)

    print("Eksperyment 2 - Macierz bot vs bot")
    print(f"  kubelki: {[(label, n, m) for label, n, m in buckets]}")
    t_desc = f"T={args.T}" if args.T is not None else f"T=max({args.t_min}, {args.t_per_n}*n)"
    print(f"  {t_desc}  n_cops={args.n_cops}  graph_type={args.graph_type}")
    print(f"  N={args.games} gier na komórkę/kubełek  master_seed={args.seed}")
    print(f"  Strategie: {[str(s) for s in strategies]}")
    print(f"  placement={args.placement}")
    print()

    results: list[dict] = []
    start = time.perf_counter()

    for bucket_label, n, m in buckets:
        T = round_limit_for_bucket(n, args)
        print(f"=== kubelek {bucket_label}: n={n}, m={m}, T={T} ===")
        for cop_spec in strategies:
            for robber_spec in strategies:
                label = f"COP={cop_spec} vs ROBBER={robber_spec}"
                print(f"--- {label} ---")
                summary = simulate_batch(
                    n=n, m=m, T=T, n_cops=args.n_cops,
                    cop_spec=cop_spec, robber_spec=robber_spec,
                    n_games=args.games, master_seed=args.seed,
                    graph_type=args.graph_type,
                    placement=args.placement,
                    progress=not args.quiet,
                    progress_prefix="  ",
                    workers=args.workers,
                )
                row = summary.as_dict()
                row["bucket"] = bucket_label
                results.append(row)
                print(f"  -> cop win-rate = {summary.win_rate:.1%}  "
                      f"mean_rounds = {summary.mean_rounds:.1f}  "
                      f"({summary.mean_seconds_per_game*1000:.1f} ms/game)\n",
                      flush=True)

    elapsed = time.perf_counter() - start

    # Save CSV
    output_path = os.path.join(args.output_dir, "exp2_bot_matrix.csv")
    write_csv(output_path, results)
    print(f"Zapisano: {output_path}")

    # Print matrix
    print()
    print("=" * 78)
    print("MACIERZ WIN-RATE POLICJANTÓW  (wiersz = strategia cop, kolumna = robber)")
    print("=" * 78)
    width = 18
    label = "cop \\ robber"
    header = f"{label:>{width}}" + "".join(
        f"{str(s):>{width}}" for s in strategies
    )
    print(header)
    print("-" * len(header))
    for bucket_label, _n, _m in buckets:
        print(f"\n[{bucket_label}]")
        for cop_spec in strategies:
            row_cells = [f"{str(cop_spec):>{width}}"]
            for robber_spec in strategies:
                r = next(x for x in results
                         if x["bucket"] == bucket_label
                         and x["cop_strategy"] == str(cop_spec)
                         and x["robber_strategy"] == str(robber_spec))
                row_cells.append(f"{r['win_rate']:>{width}.1%}")
            print("".join(row_cells))
    print()
    print(f"Czas laczny: {elapsed:.1f} s")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Eksperyment 2: macierz bot vs bot.")
    p.add_argument("--games", type=int, default=100, help="liczba gier na komórkę/kubełek (default: 100)")
    p.add_argument("--buckets", nargs="+",
                   choices=[label for label, _n, _m in DEFAULT_BUCKETS],
                   default=[label for label, _n, _m in DEFAULT_BUCKETS],
                   help="kubełki grafów do uruchomienia")
    p.add_argument("--n", type=int, default=None, help="custom: liczba wierzchołków; pomija --buckets")
    p.add_argument("--m", type=int, default=None, help="custom: liczba krawędzi; pomija --buckets")
    p.add_argument("--T", type=int, default=None,
                   help="stały limit rund; jeśli pominięty, używa T=max(t-min, t-per-n*n)")
    p.add_argument("--t-per-n", type=float, default=5 / 3,
                   help="domyślne T proporcjonalne do n (default: 5/3; daje T=50 dla n=30)")
    p.add_argument("--t-min", type=int, default=20,
                   help="minimalne T przy automatycznym limicie rund (default: 20)")
    p.add_argument("--n-cops", type=int, default=1, help="liczba policjantów (default: 1)")
    p.add_argument("--seed", type=int, default=42, help="master seed (default: 42)")
    p.add_argument("--graph-type", choices=["any", "tree", "planar"], default="any")
    p.add_argument("--placement", choices=["random", "heuristic"], default="heuristic")
    p.add_argument("--no-minimax", action="store_true", help="pomiń kolumny/wiersze minimax (szybciej)")
    p.add_argument("--minimax-depth", type=int, default=3, help="głębokość minimax (default: 3)")
    p.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="katalog na wyniki CSV")
    p.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1),
                   help="liczba procesów roboczych (default: liczba CPU - 1)")
    p.add_argument("--quiet", action="store_true", help="ukryj progress")
    args = p.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
