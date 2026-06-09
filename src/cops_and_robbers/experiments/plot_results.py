"""Generate charts from experiment CSV outputs.

Reads CSVs produced by the experiment scripts and saves PNG charts alongside
them. Designed to be importable from a notebook or run from the CLI.

Usage::

    python -m cops_and_robbers.experiments.plot_results
    python -m cops_and_robbers.experiments.plot_results --results-dir results --exp 2 3 4
"""

from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict


# ----------------------------------------------------------------------------
# Color palette tied to the game's own colors (consistent with presentation)
# ----------------------------------------------------------------------------
COLOR_COP = "#3C78FF"
COLOR_ROBBER = "#E64646"
COLOR_YELLOW = "#F5C400"
COLOR_NAVY = "#1A2845"
COLOR_MUTED = "#5C5C5C"
COLOR_RULE = "#C9C2B5"

STRATEGY_COLORS = {
    "random": COLOR_MUTED,
    "greedy": COLOR_COP,
}


def _import_matplotlib():
    try:
        import matplotlib
        matplotlib.use("Agg")  # non-interactive backend (no display needed)
        import matplotlib.pyplot as plt
        return plt
    except ImportError as exc:
        raise SystemExit(
            "matplotlib is required for plotting. Install with: pip install matplotlib"
        ) from exc


def _strategy_color(strategy: str) -> str:
    """Pick a color for a strategy label like 'random', 'greedy', 'minimax(d=3)'."""
    if strategy.startswith("minimax"):
        return COLOR_ROBBER
    return STRATEGY_COLORS.get(strategy, COLOR_NAVY)


def _read_csv(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ----------------------------------------------------------------------------
# Experiment 2 — Bot vs Bot matrix
# ----------------------------------------------------------------------------

def plot_exp2(csv_path: str, output_path: str) -> None:
    """Heatmap-style table: cop strategy (rows) × robber strategy (cols)."""
    plt = _import_matplotlib()
    rows = _read_csv(csv_path)

    cop_strategies = []
    robber_strategies = []
    for r in rows:
        if r["cop_strategy"] not in cop_strategies:
            cop_strategies.append(r["cop_strategy"])
        if r["robber_strategy"] not in robber_strategies:
            robber_strategies.append(r["robber_strategy"])

    win_rate = {}
    for r in rows:
        win_rate[(r["cop_strategy"], r["robber_strategy"])] = float(r["win_rate"])

    fig, ax = plt.subplots(figsize=(7, 5))
    data = [
        [win_rate.get((c, r), 0.0) for r in robber_strategies]
        for c in cop_strategies
    ]

    im = ax.imshow(data, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(robber_strategies)), robber_strategies)
    ax.set_yticks(range(len(cop_strategies)), cop_strategies)
    ax.set_xlabel("Strategia złodzieja", color=COLOR_NAVY)
    ax.set_ylabel("Strategia policjanta", color=COLOR_NAVY)
    ax.set_title("Eksperyment 1 — Macierz win-rate policjantów",
                 color=COLOR_NAVY, weight="bold", pad=14)

    # Annotate cells
    for i, c in enumerate(cop_strategies):
        for j, r in enumerate(robber_strategies):
            val = data[i][j]
            text_color = "white" if val < 0.4 or val > 0.7 else COLOR_NAVY
            ax.text(j, i, f"{val:.1%}",
                    ha="center", va="center", color=text_color, weight="bold")

    fig.colorbar(im, ax=ax, label="win-rate policjantów")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, facecolor="white")
    plt.close(fig)
    print(f"Wykres: {output_path}")


# ----------------------------------------------------------------------------
# Experiment 3 — Size sweep (line chart)
# ----------------------------------------------------------------------------

def plot_exp3(csv_path: str, output_path: str) -> None:
    """Line chart of win-rate vs n for each comparison variant."""
    plt = _import_matplotlib()
    rows = _read_csv(csv_path)

    # Group by comparison label
    series: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for r in rows:
        label = r.get("comparison_label", r["cop_strategy"])
        series[label].append((int(r["n"]), float(r["win_rate"])))
    for label in series:
        series[label].sort()

    fig, ax = plt.subplots(figsize=(8, 5))
    colors_cycle = [COLOR_COP, COLOR_ROBBER, COLOR_YELLOW, COLOR_MUTED, COLOR_NAVY]
    for i, (label, points) in enumerate(series.items()):
        xs = [p[0] for p in points]
        ys = [p[1] * 100 for p in points]  # convert to %
        color = colors_cycle[i % len(colors_cycle)]
        ax.plot(xs, ys, marker="o", label=label, color=color, linewidth=2)

    ax.set_xlabel("n (liczba wierzchołków)", color=COLOR_NAVY)
    ax.set_ylabel("win-rate policjantów [%]", color=COLOR_NAVY)
    ax.set_title("Eksperyment 2 — Wpływ rozmiaru grafu",
                 color=COLOR_NAVY, weight="bold", pad=14)
    ax.set_ylim(-2, 105)
    ax.axhline(50, color=COLOR_RULE, linestyle="--", linewidth=0.8, zorder=0)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", framealpha=0.95)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, facecolor="white")
    plt.close(fig)
    print(f"Wykres: {output_path}")


# ----------------------------------------------------------------------------
# Experiment 4 — Cops × type (grouped bar chart)
# ----------------------------------------------------------------------------

def plot_exp4(csv_path: str, output_path: str) -> None:
    """Grouped bar chart: x = graph type, group = k."""
    plt = _import_matplotlib()
    rows = _read_csv(csv_path)

    graph_types = sorted({r["graph_type"] for r in rows})
    k_values = sorted({int(r["n_cops"]) for r in rows})

    win_rate = {}
    for r in rows:
        win_rate[(int(r["n_cops"]), r["graph_type"])] = float(r["win_rate"]) * 100

    fig, ax = plt.subplots(figsize=(8, 5))
    n_groups = len(graph_types)
    n_bars = len(k_values)
    width = 0.8 / n_bars
    indices = list(range(n_groups))

    colors_for_k = [COLOR_MUTED, COLOR_COP, COLOR_ROBBER, COLOR_YELLOW]
    for i, k in enumerate(k_values):
        heights = [win_rate.get((k, gt), 0.0) for gt in graph_types]
        offsets = [x + (i - n_bars / 2 + 0.5) * width for x in indices]
        bars = ax.bar(offsets, heights, width=width * 0.9,
                      label=f"k={k}", color=colors_for_k[i % len(colors_for_k)])
        for rect, h in zip(bars, heights):
            ax.text(rect.get_x() + rect.get_width() / 2, h + 1,
                    f"{h:.0f}", ha="center", va="bottom",
                    fontsize=9, color=COLOR_NAVY)

    ax.set_xticks(indices, graph_types)
    ax.set_xlabel("Typ grafu", color=COLOR_NAVY)
    ax.set_ylabel("win-rate policjantów [%]", color=COLOR_NAVY)
    ax.set_title("Eksperyment 3 — Liczba policjantów × typ grafu",
                 color=COLOR_NAVY, weight="bold", pad=14)
    ax.set_ylim(0, 112)
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend(title="Liczba policjantów", loc="lower right", framealpha=0.95)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, facecolor="white")
    plt.close(fig)
    print(f"Wykres: {output_path}")


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Wykresy z wyników eksperymentów.")
    p.add_argument("--results-dir", default="results",
                   help="katalog z plikami CSV (default: results)")
    p.add_argument("--exp", type=int, nargs="+", default=[2, 3, 4],
                   choices=[2, 3, 4],
                   help="które eksperymenty zwizualizować (default: 2 3 4)")
    args = p.parse_args(argv)

    plotters = {
        2: ("exp2_bot_matrix.csv",     "exp2_bot_matrix.png",     plot_exp2),
        3: ("exp3_size_sweep.csv",     "exp3_size_sweep.png",     plot_exp3),
        4: ("exp4_cops_x_type.csv",    "exp4_cops_x_type.png",    plot_exp4),
    }
    for exp_num in args.exp:
        csv_name, png_name, fn = plotters[exp_num]
        csv_path = os.path.join(args.results_dir, csv_name)
        png_path = os.path.join(args.results_dir, png_name)
        if not os.path.exists(csv_path):
            print(f"Brak: {csv_path}  (najpierw uruchom odpowiedni eksperyment)")
            continue
        fn(csv_path, png_path)


if __name__ == "__main__":
    main()
