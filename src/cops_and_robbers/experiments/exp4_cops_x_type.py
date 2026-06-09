"""Experiment 4 — Liczba policjantów × typ grafu (slide 17).

Tests the impact of the number of cops on win-rate across the three graph
types. Directly probes the Aigner–Fromme bound and the trees-cop-win theorem.

Default configuration matches the WIP placeholder on slide 17:
  k in {1, 2, 3}, graph_type in {any, tree, planar}, n=12, T=30, N=200 games.
  Both sides use minimax with depths matching the "Expert" preset in app.py:
  d_cop = 5 for k=1, d=3 for k=2, d=3 for k=3.

Theoretical predictions to verify:
  * trees,    k=1   → ~100% cop wins  (c(tree) = 1)
  * planar,   k=3   → very high       (Aigner–Fromme: c(planar) ≤ 3)
  * any,      k=1   → likely modest   (general graphs may have c > 1)

Usage::

    python -m cops_and_robbers.experiments.exp4_cops_x_type
    python -m cops_and_robbers.experiments.exp4_cops_x_type --games 50
    python -m cops_and_robbers.experiments.exp4_cops_x_type --bot greedy   # faster
"""

from __future__ import annotations

import argparse
import os
import time

from cops_and_robbers.experiments.runner import (
    BotSpec, simulate_batch, write_csv, clamp_edge_count,
)


DEFAULT_OUTPUT_DIR = "results"

# Mirrors the "Expert" preset from app.py
EXPERT_COP_DEPTH = {1: 5, 2: 3, 3: 3}
EXPERT_ROBBER_DEPTH = {1: 5, 2: 3, 3: 3}


def build_specs(bot_kind: str, n_cops: int) -> tuple[BotSpec, BotSpec]:
    if bot_kind == "minimax":
        return (
            BotSpec("minimax", depth=EXPERT_COP_DEPTH[n_cops]),
            BotSpec("minimax", depth=EXPERT_ROBBER_DEPTH[n_cops]),
        )
    if bot_kind == "greedy":
        return BotSpec("greedy"), BotSpec("greedy")
    if bot_kind == "random":
        return BotSpec("random"), BotSpec("random")
    raise ValueError(bot_kind)


def run(args: argparse.Namespace) -> None:
    print(f"Eksperyment 4 — Liczba policjantów × typ grafu")
    print(f"  n={args.n}  m={args.m}  T={args.T}")
    print(f"  k ∈ {args.k_values}   typy: {args.graph_types}")
    print(f"  N={args.games} gier na konfigurację   master_seed={args.seed}")
    print(f"  Strategie: {args.bot}  placement={args.placement}")
    print()

    rows: list[dict] = []
    start = time.perf_counter()

    for k in args.k_values:
        if k < 1:
            continue
        cop_spec, robber_spec = build_specs(args.bot, k)
        for graph_type in args.graph_types:
            # Trees have exactly n-1 edges; clamp m to the legal range.
            m_eff = clamp_edge_count(args.n, args.m, graph_type)
            label = f"k={k}, typ={graph_type}"
            print(f"--- {label}  (m={m_eff}, cop={cop_spec}, robber={robber_spec}) ---",
                  flush=True)
            try:
                summary = simulate_batch(
                    n=args.n, m=m_eff, T=args.T, n_cops=k,
                    cop_spec=cop_spec, robber_spec=robber_spec,
                    n_games=args.games, master_seed=args.seed,
                    graph_type=graph_type,
                    placement=args.placement,
                    progress=not args.quiet,
                    progress_prefix="  ",
                )
            except Exception as exc:
                print(f"  ! pominięte: {exc}")
                continue
            row = summary.as_dict()
            row["k"] = k
            rows.append(row)
            print(f"  → cop win-rate = {summary.win_rate:.1%}  "
                  f"mean_rounds = {summary.mean_rounds:.1f}  "
                  f"({summary.mean_seconds_per_game*1000:.0f} ms/game)\n",
                  flush=True)

    elapsed = time.perf_counter() - start

    output_path = os.path.join(args.output_dir, "exp4_cops_x_type.csv")
    write_csv(output_path, rows)
    print(f"Zapisano: {output_path}")

    # Print summary table
    print()
    print("=" * 64)
    print("WIN-RATE POLICJANTÓW  (wiersz = k, kolumna = typ grafu)")
    print("=" * 64)
    width = 14
    label = "k \\ typ"
    header = f"{label:>{width}}" + "".join(
        f"{gt:>{width}}" for gt in args.graph_types
    )
    print(header)
    print("-" * len(header))
    for k in args.k_values:
        row_cells = [f"{k:>{width}}"]
        for graph_type in args.graph_types:
            cell = next(
                (r for r in rows if r["n_cops"] == k and r["graph_type"] == graph_type),
                None,
            )
            row_cells.append(f"{cell['win_rate']:>{width}.1%}" if cell else f"{'—':>{width}}")
        print("".join(row_cells))
    print()
    print(f"Czas łączny: {elapsed:.1f} s")
    print()
    print("Oczekiwane: drzewa @ k=1 ≈ 100%, planarne @ k=3 ≈ 100%,")
    print("           dowolne @ k=1 — niższe niż przy k=3.")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Eksperyment 4: liczba policjantów × typ grafu.")
    p.add_argument("--games", type=int, default=200, help="liczba gier na konfigurację (default: 200)")
    p.add_argument("--n", type=int, default=12, help="liczba wierzchołków (default: 12)")
    p.add_argument("--m", type=int, default=18, help="liczba krawędzi (auto-clampowane do typu grafu)")
    p.add_argument("--T", type=int, default=30, help="limit rund (default: 30)")
    p.add_argument("--k-values", type=int, nargs="+", default=[1, 2, 3],
                   help="wartości k (liczby policjantów); default: 1 2 3")
    p.add_argument("--graph-types", nargs="+",
                   choices=["any", "tree", "planar"],
                   default=["any", "tree", "planar"])
    p.add_argument("--bot", choices=["random", "greedy", "minimax"], default="minimax",
                   help="rodzaj botów (default: minimax expert)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--placement", choices=["random", "heuristic"], default="random")
    p.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
