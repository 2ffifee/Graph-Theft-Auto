"""Experiment 3 — Wpływ rozmiaru grafu na win-rate (slide 16).

Sweeps the number of vertices n across a configurable set, keeping the
average density m/n fixed. For each (n, bot configuration) point plays N games
and records cop win-rate.

Default configuration matches the WIP placeholder on slide 16:
  n in {5, 8, 10, 15, 20, 25, 30}, m/n = 1.5, T = 2n, N = 200 per point.

By default compares Random / Greedy / Minimax(d=3) cop strategies against two
fixed robber variants: Greedy and Minimax(d=3).

Usage::

    python -m cops_and_robbers.experiments.exp3_size_sweep
    python -m cops_and_robbers.experiments.exp3_size_sweep --games 50
    python -m cops_and_robbers.experiments.exp3_size_sweep --n-values 5 10 20
"""

from __future__ import annotations

import argparse
import os
import time

from cops_and_robbers.experiments.runner import (
    BotSpec, simulate_batch, write_csv, clamp_edge_count,
)


DEFAULT_OUTPUT_DIR = "results"
DEFAULT_N_VALUES = [5, 8, 10, 15, 20, 25, 30]


def build_comparison(args: argparse.Namespace) -> list[tuple[BotSpec, BotSpec, str]]:
    """Return list of (cop_spec, robber_spec, label) tuples to compare."""
    comparisons: list[tuple[BotSpec, BotSpec, str]] = []

    if args.compare == "cop-strategies":
        # Fixed robber strategy, vary cop strategy
        for robber_kind in args.robber_strategies:
            robber = BotSpec(robber_kind)
            if robber_kind == "minimax":
                robber = BotSpec("minimax", depth=args.robber_minimax_depth)
            for cop_kind in ["random", "greedy"]:
                comparisons.append((BotSpec(cop_kind), robber, f"COP={cop_kind} vs ROBBER={robber}"))
            if not args.no_minimax:
                comparisons.append(
                    (BotSpec("minimax", depth=args.cop_minimax_depth), robber,
                     f"COP=minimax(d={args.cop_minimax_depth}) vs ROBBER={robber}")
                )
    elif args.compare == "robber-strategies":
        # Fixed cop strategy, vary robber strategy
        cop = BotSpec(args.cop_strategy)
        if args.cop_strategy == "minimax":
            cop = BotSpec("minimax", depth=args.cop_minimax_depth)
        for robber_kind in ["random", "greedy"]:
            comparisons.append((cop, BotSpec(robber_kind), f"ROBBER={robber_kind}"))
        if not args.no_minimax:
            comparisons.append(
                (cop, BotSpec("minimax", depth=args.robber_minimax_depth),
                 f"ROBBER=minimax(d={args.robber_minimax_depth})")
            )
    else:
        raise ValueError(args.compare)

    return comparisons


def m_for_n(n: int, ratio: float, graph_type: str) -> int:
    """Compute m for a given n preserving (approximately) the m/n ratio,
    clamped to the legal range for that graph type."""
    target = round(ratio * n)
    return clamp_edge_count(n, target, graph_type)


def t_for_n(n: int, t_per_n: float, t_min: int) -> int:
    return max(t_min, int(round(t_per_n * n)))


def run(args: argparse.Namespace) -> None:
    comparisons = build_comparison(args)

    print("Eksperyment 3 - Wplyw rozmiaru grafu na win-rate")
    print(f"  n in {args.n_values}")
    print(f"  m/n = {args.density}   T = {args.t_per_n} * n  (min {args.t_min})")
    print(f"  n_cops={args.n_cops}  graph_type={args.graph_type}  placement={args.placement}")
    print(f"  N={args.games} gier na punkt   master_seed={args.seed}")
    print(f"  Porownania ({args.compare}): {[lbl for _, _, lbl in comparisons]}")
    print()

    rows: list[dict] = []
    start = time.perf_counter()

    for n in args.n_values:
        m = m_for_n(n, args.density, args.graph_type)
        T = t_for_n(n, args.t_per_n, args.t_min)
        if n < args.n_cops + 1:
            print(f"  pomijam n={n} (potrzeba >= {args.n_cops + 1} wierzcholkow)")
            continue
        for cop_spec, robber_spec, label in comparisons:
            print(f"--- n={n}  m={m}  T={T}  {label} ---", flush=True)
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
            row["comparison_label"] = label
            rows.append(row)
            print(f"  -> cop win-rate = {summary.win_rate:.1%}  "
                  f"mean_rounds = {summary.mean_rounds:.1f}  "
                  f"({summary.mean_seconds_per_game*1000:.0f} ms/game)\n",
                  flush=True)

    elapsed = time.perf_counter() - start

    output_path = os.path.join(args.output_dir, "exp3_size_sweep.csv")
    write_csv(output_path, rows)
    print(f"Zapisano: {output_path}")
    print(f"Czas laczny: {elapsed:.1f} s")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Eksperyment 3: wpływ rozmiaru grafu.")
    p.add_argument("--games", type=int, default=100, help="liczba gier na punkt (default: 100)")
    p.add_argument("--n-values", type=int, nargs="+", default=DEFAULT_N_VALUES,
                   help=f"wartości n (default: {DEFAULT_N_VALUES})")
    p.add_argument("--density", type=float, default=1.5, help="stosunek m/n (default: 1.5)")
    p.add_argument("--t-per-n", type=float, default=2.0, help="T = t_per_n × n (default: 2.0)")
    p.add_argument("--t-min", type=int, default=10, help="minimalne T (default: 10)")
    p.add_argument("--n-cops", type=int, default=1, help="liczba policjantów (default: 1)")
    p.add_argument("--seed", type=int, default=42, help="master seed (default: 42)")
    p.add_argument("--graph-type", choices=["any", "tree", "planar"], default="any")
    p.add_argument("--placement", choices=["random", "heuristic"], default="heuristic")
    p.add_argument("--compare", choices=["cop-strategies", "robber-strategies"],
                   default="cop-strategies",
                   help="czy porównujemy strategie policjanta czy złodzieja")
    p.add_argument("--cop-strategy", choices=["random", "greedy", "minimax"], default="greedy",
                   help="strategia policjanta gdy compare=robber-strategies (default: greedy)")
    p.add_argument("--robber-strategies", choices=["random", "greedy", "minimax"],
                   nargs="+", default=["greedy", "minimax"],
                   help="strategie złodzieja gdy compare=cop-strategies (default: greedy minimax)")
    p.add_argument("--no-minimax", action="store_true",
                   help="pomiń wariant minimax (znacznie szybciej dla dużych n)")
    p.add_argument("--cop-minimax-depth", type=int, default=3,
                   help="głębokość minimax dla policjanta (default: 3)")
    p.add_argument("--robber-minimax-depth", type=int, default=3,
                   help="głębokość minimax dla złodzieja (default: 3)")
    p.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    p.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1),
                   help="liczba procesów roboczych (default: liczba CPU - 1)")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
