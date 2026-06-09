"""Experiment 2 — Bot vs Bot matrix (slide 15).

For each pair (cop strategy, robber strategy) in the chosen set, plays N games
on freshly generated graphs and reports the cop win-rate.

Default configuration matches the WIP placeholder on slide 15:
  n=12, m=18, T=30, 1 cop, N=1000 games per cell, graph_type=any.

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


def build_strategy_set(include_minimax: bool, minimax_depth: int) -> list[BotSpec]:
    specs = [BotSpec("random"), BotSpec("greedy")]
    if include_minimax:
        specs.append(BotSpec("minimax", depth=minimax_depth))
    return specs


def run(args: argparse.Namespace) -> None:
    strategies = build_strategy_set(
        include_minimax=not args.no_minimax,
        minimax_depth=args.minimax_depth,
    )

    print(f"Eksperyment 2 — Macierz bot vs bot")
    print(f"  n={args.n}  m={args.m}  T={args.T}  n_cops={args.n_cops}  "
          f"graph_type={args.graph_type}")
    print(f"  N={args.games} gier na komórkę  master_seed={args.seed}")
    print(f"  Strategie: {[str(s) for s in strategies]}")
    print()

    results: list[dict] = []
    start = time.perf_counter()

    for cop_spec in strategies:
        for robber_spec in strategies:
            label = f"COP={cop_spec} vs ROBBER={robber_spec}"
            print(f"--- {label} ---")
            summary = simulate_batch(
                n=args.n, m=args.m, T=args.T, n_cops=args.n_cops,
                cop_spec=cop_spec, robber_spec=robber_spec,
                n_games=args.games, master_seed=args.seed,
                graph_type=args.graph_type,
                placement=args.placement,
                progress=not args.quiet,
                progress_prefix="  ",
            )
            row = summary.as_dict()
            results.append(row)
            print(f"  → cop win-rate = {summary.win_rate:.1%}  "
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
    for cop_spec in strategies:
        row_cells = [f"{str(cop_spec):>{width}}"]
        for robber_spec in strategies:
            r = next(x for x in results
                     if x["cop_strategy"] == str(cop_spec)
                     and x["robber_strategy"] == str(robber_spec))
            row_cells.append(f"{r['win_rate']:>{width}.1%}")
        print("".join(row_cells))
    print()
    print(f"Czas łączny: {elapsed:.1f} s")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Eksperyment 2: macierz bot vs bot.")
    p.add_argument("--games", type=int, default=1000, help="liczba gier na komórkę (default: 1000)")
    p.add_argument("--n", type=int, default=12, help="liczba wierzchołków (default: 12)")
    p.add_argument("--m", type=int, default=18, help="liczba krawędzi (default: 18)")
    p.add_argument("--T", type=int, default=30, help="limit rund (default: 30)")
    p.add_argument("--n-cops", type=int, default=1, help="liczba policjantów (default: 1)")
    p.add_argument("--seed", type=int, default=42, help="master seed (default: 42)")
    p.add_argument("--graph-type", choices=["any", "tree", "planar"], default="any")
    p.add_argument("--placement", choices=["random", "heuristic"], default="random")
    p.add_argument("--no-minimax", action="store_true", help="pomiń kolumny/wiersze minimax (szybciej)")
    p.add_argument("--minimax-depth", type=int, default=3, help="głębokość minimax (default: 3)")
    p.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="katalog na wyniki CSV")
    p.add_argument("--quiet", action="store_true", help="ukryj progress")
    args = p.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
