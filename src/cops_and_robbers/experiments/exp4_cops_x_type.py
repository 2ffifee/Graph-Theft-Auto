"""Experiment 4 — Liczba policjantów × typ grafu (slide 17).

Tests the impact of the number of cops on win-rate across the three graph
types. Directly probes the Aigner–Fromme bound and the trees-cop-win theorem.

Default configuration:
  k in {1, 2, 3}, graph_type in {any, tree, planar},
  four graph buckets (n=12/30, sparse/dense), T=20/50, N=10 games.
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
DEFAULT_BUCKETS = [
    ("n12_sparse", 12, 18),
    ("n12_dense", 12, 30),
    ("n30_sparse", 30, 45),
    ("n30_dense", 30, 75),
]

def build_specs(bot_kind: str, n_cops: int, minimax_depth: int) -> tuple[BotSpec, BotSpec]:
    if bot_kind == "minimax":
        return (
            BotSpec("adaptive_minimax", depth=minimax_depth),
            BotSpec("adaptive_minimax", depth=minimax_depth),
        )
    if bot_kind == "greedy":
        return BotSpec("greedy"), BotSpec("greedy")
    if bot_kind == "random":
        return BotSpec("random"), BotSpec("random")
    raise ValueError(bot_kind)


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
    buckets = selected_buckets(args)
    t_desc = f"T={args.T}" if args.T is not None else f"T=max({args.t_min}, {args.t_per_n}*n)"

    print("Eksperyment 4 - Liczba policjantow x typ grafu")
    print(f"  kubelki: {[(label, n, m) for label, n, m in buckets]}  {t_desc}")
    print(f"  k in {args.k_values}   typy: {args.graph_types}")
    print(f"  N={args.games} gier na konfiguracje   master_seed={args.seed}")
    print(f"  Strategie: {args.bot}  placement={args.placement}")
    print()

    rows: list[dict] = []
    start = time.perf_counter()

    for k in args.k_values:
        if k < 1:
            continue
        cop_spec, robber_spec = build_specs(args.bot, k, args.minimax_depth)
        for bucket_label, n, m in buckets:
            T = round_limit_for_bucket(n, args)
            for graph_type in args.graph_types:
                # Trees have exactly n-1 edges; planar graphs have at most 3n-6.
                m_eff = clamp_edge_count(n, m, graph_type)
                label = f"k={k}, kubelek={bucket_label}, typ={graph_type}"
                print(f"--- {label}  (n={n}, m={m_eff}, T={T}, cop={cop_spec}, robber={robber_spec}) ---",
                      flush=True)
                try:
                    summary = simulate_batch(
                        n=n, m=m_eff, T=T, n_cops=k,
                        cop_spec=cop_spec, robber_spec=robber_spec,
                        n_games=args.games, master_seed=args.seed,
                        graph_type=graph_type,
                        placement=args.placement,
                        progress=not args.quiet,
                        progress_prefix="  ",
                        workers=args.workers,
                    )
                except Exception as exc:
                    print(f"  ! pominiete: {exc}")
                    continue
                row = summary.as_dict()
                row["k"] = k
                row["bucket"] = bucket_label
                rows.append(row)
                print(f"  -> cop win-rate = {summary.win_rate:.1%}  "
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
    for bucket_label, _n, _m in buckets:
        print(f"\n[{bucket_label}]")
        for k in args.k_values:
            row_cells = [f"{k:>{width}}"]
            for graph_type in args.graph_types:
                cell = next(
                    (r for r in rows
                     if r["bucket"] == bucket_label
                     and r["n_cops"] == k
                     and r["graph_type"] == graph_type),
                    None,
                )
                row_cells.append(f"{cell['win_rate']:>{width}.1%}" if cell else f"{'-':>{width}}")
            print("".join(row_cells))
    print()
    print(f"Czas laczny: {elapsed:.1f} s")
    print()
    print("Oczekiwane: drzewa @ k=1 ~= 100%, planarne @ k=3 ~= 100%,")
    print("           dowolne @ k=1 - nizsze niz przy k=3.")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Eksperyment 4: liczba policjantów × typ grafu.")
    p.add_argument("--games", type=int, default=20, help="liczba gier na konfigurację (default: 20)")
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
    p.add_argument("--k-values", type=int, nargs="+", default=[1, 2, 3],
                   help="wartości k (liczby policjantów); default: 1 2 3")
    p.add_argument("--graph-types", nargs="+",
                   choices=["any", "tree", "planar"],
                   default=["any", "tree", "planar"])
    p.add_argument("--bot", choices=["random", "greedy", "minimax"], default="minimax",
                   help="rodzaj botów (default: minimax expert)")
    p.add_argument("--minimax-depth", type=int, default=3,
                   help="bazowa głębokość minimax dla --bot minimax (default: 3; adaptacyjnie obcinana przy dużym branching)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--placement", choices=["random", "heuristic"], default="heuristic")
    p.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    p.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1),
                   help="liczba procesów roboczych (default: liczba CPU - 1)")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
