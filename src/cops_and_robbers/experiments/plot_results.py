"""Generate charts from experiment CSV outputs."""

from __future__ import annotations

import argparse
import csv
import math
import os
import re
from collections import defaultdict
from collections.abc import Iterable


COLOR_COP = "#3C78FF"
COLOR_ROBBER = "#E64646"
COLOR_YELLOW = "#F5C400"
COLOR_NAVY = "#1A2845"
COLOR_MUTED = "#5C5C5C"
COLOR_RULE = "#C9C2B5"


def _import_matplotlib():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except ImportError as exc:
        raise SystemExit(
            "matplotlib is required for plotting. Install with: pip install matplotlib"
        ) from exc


def _read_csv(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _ordered_unique(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def _row_bucket(row: dict) -> str:
    return row.get("bucket") or f"n={row['n']}, m={row['m']}"


def _with_suffix(path: str, suffix: str) -> str:
    root, ext = os.path.splitext(path)
    return f"{root}_{suffix}{ext}"


def _filename_slug(value: str) -> str:
    slug = value.lower()
    slug = slug.replace("minimax(d=3,adaptive)", "minimax_adaptive")
    slug = slug.replace("minimax(d=3)", "minimax")
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")


def plot_exp2(csv_path: str, output_path: str) -> None:
    """Save one heatmap per graph bucket."""
    plt = _import_matplotlib()
    rows = _read_csv(csv_path)

    cop_strategies = _ordered_unique(row["cop_strategy"] for row in rows)
    robber_strategies = _ordered_unique(row["robber_strategy"] for row in rows)
    buckets = _ordered_unique(_row_bucket(row) for row in rows)

    for bucket in buckets:
        bucket_rows = [row for row in rows if _row_bucket(row) == bucket]
        win_rate = {
            (row["cop_strategy"], row["robber_strategy"]): float(row["win_rate"])
            for row in bucket_rows
        }
        data = [
            [win_rate.get((cop, robber), 0.0) for robber in robber_strategies]
            for cop in cop_strategies
        ]

        fig, ax = plt.subplots(figsize=(7.8, 5.4))
        image = ax.imshow(data, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
        ax.set_xticks(range(len(robber_strategies)), robber_strategies, rotation=20, ha="right")
        ax.set_yticks(range(len(cop_strategies)), cop_strategies)
        ax.set_xlabel("Strategia złodzieja", color=COLOR_NAVY)
        ax.set_ylabel("Strategia policjanta", color=COLOR_NAVY)
        ax.set_title(f"Eksperyment 2 - {bucket}", color=COLOR_NAVY, weight="bold", pad=12)

        for i, cop in enumerate(cop_strategies):
            for j, robber in enumerate(robber_strategies):
                value = data[i][j]
                text_color = "white" if value < 0.4 or value > 0.7 else COLOR_NAVY
                ax.text(j, i, f"{value:.1%}", ha="center", va="center",
                        color=text_color, weight="bold")

        fig.colorbar(image, ax=ax, label="win-rate policjantów")
        fig.tight_layout()
        bucket_path = _with_suffix(output_path, _filename_slug(bucket))
        fig.savefig(bucket_path, dpi=150, facecolor="white")
        plt.close(fig)
        print(f"Wykres: {bucket_path}")


def plot_exp3(csv_path: str, output_path: str) -> None:
    """Save one line chart per fixed robber strategy."""
    plt = _import_matplotlib()
    rows = _read_csv(csv_path)

    robber_strategies = _ordered_unique(row["robber_strategy"] for row in rows)
    colors_cycle = [COLOR_COP, COLOR_ROBBER, COLOR_YELLOW, COLOR_MUTED, COLOR_NAVY, "#2E8B57"]

    for robber_strategy in robber_strategies:
        robber_rows = [row for row in rows if row["robber_strategy"] == robber_strategy]
        series: dict[str, list[tuple[int, float]]] = defaultdict(list)
        for row in robber_rows:
            series[row["cop_strategy"]].append((int(row["n"]), float(row["win_rate"])))
        for label in series:
            series[label].sort()

        fig, ax = plt.subplots(figsize=(8.8, 5.6))
        for i, (label, points) in enumerate(series.items()):
            xs = [point[0] for point in points]
            ys = [point[1] * 100 for point in points]
            ax.plot(xs, ys, marker="o", label=f"COP={label}",
                    color=colors_cycle[i % len(colors_cycle)], linewidth=2)

        ax.set_xlabel("n (liczba wierzchołków)", color=COLOR_NAVY)
        ax.set_ylabel("win-rate policjantów [%]", color=COLOR_NAVY)
        ax.set_title(f"Eksperyment 3 - złodziej: {robber_strategy}",
                     color=COLOR_NAVY, weight="bold", pad=14)
        ax.set_ylim(-2, 105)
        ax.axhline(50, color=COLOR_RULE, linestyle="--", linewidth=0.8, zorder=0)
        ax.grid(True, alpha=0.25)
        ax.legend(loc="best", framealpha=0.95)
        fig.tight_layout()
        robber_path = _with_suffix(output_path, f"robber_{_filename_slug(robber_strategy)}")
        fig.savefig(robber_path, dpi=150, facecolor="white")
        plt.close(fig)
        print(f"Wykres: {robber_path}")


def plot_exp4(csv_path: str, output_path: str) -> None:
    """Grouped bar chart: graph type x cop count, per bucket."""
    plt = _import_matplotlib()
    rows = _read_csv(csv_path)

    graph_types = sorted({row["graph_type"] for row in rows})
    k_values = sorted({int(row["n_cops"]) for row in rows})
    buckets = _ordered_unique(_row_bucket(row) for row in rows)

    ncols = 2 if len(buckets) > 1 else 1
    nrows = math.ceil(len(buckets) / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(8 * ncols, 4.8 * nrows), squeeze=False)
    n_groups = len(graph_types)
    n_bars = len(k_values)
    width = 0.8 / n_bars
    indices = list(range(n_groups))
    colors_for_k = [COLOR_MUTED, COLOR_COP, COLOR_ROBBER, COLOR_YELLOW]

    for ax, bucket in zip(axes.flat, buckets):
        bucket_rows = [row for row in rows if _row_bucket(row) == bucket]
        win_rate = {
            (int(row["n_cops"]), row["graph_type"]): float(row["win_rate"]) * 100
            for row in bucket_rows
        }

        for i, k in enumerate(k_values):
            heights = [win_rate.get((k, graph_type), 0.0) for graph_type in graph_types]
            offsets = [x + (i - n_bars / 2 + 0.5) * width for x in indices]
            bars = ax.bar(offsets, heights, width=width * 0.9,
                          label=f"k={k}", color=colors_for_k[i % len(colors_for_k)])
            for rect, height in zip(bars, heights):
                ax.text(rect.get_x() + rect.get_width() / 2, height + 1,
                        f"{height:.0f}", ha="center", va="bottom",
                        fontsize=9, color=COLOR_NAVY)

        ax.set_xticks(indices, graph_types)
        ax.set_xlabel("Typ grafu", color=COLOR_NAVY)
        ax.set_ylabel("win-rate policjantów [%]", color=COLOR_NAVY)
        ax.set_title(bucket, color=COLOR_NAVY, weight="bold", pad=10)
        ax.set_ylim(0, 112)
        ax.grid(True, axis="y", alpha=0.25)
        ax.legend(title="Liczba policjantów", loc="lower right", framealpha=0.95)

    for ax in axes.flat[len(buckets):]:
        ax.axis("off")

    fig.suptitle("Eksperyment 4 - liczba policjantów x typ grafu",
                 color=COLOR_NAVY, weight="bold", y=0.995)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, facecolor="white")
    plt.close(fig)
    print(f"Wykres: {output_path}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Wykresy z wyników eksperymentów.")
    parser.add_argument("--results-dir", default="results",
                        help="katalog z plikami CSV (default: results)")
    parser.add_argument("--exp", type=int, nargs="+", default=[2, 3, 4],
                        choices=[2, 3, 4],
                        help="które eksperymenty zwizualizować (default: 2 3 4)")
    args = parser.parse_args(argv)

    plotters = {
        2: ("exp2_bot_matrix.csv", "exp2_bot_matrix.png", plot_exp2),
        3: ("exp3_size_sweep.csv", "exp3_size_sweep.png", plot_exp3),
        4: ("exp4_cops_x_type.csv", "exp4_cops_x_type.png", plot_exp4),
    }
    for exp_num in args.exp:
        csv_name, png_name, plot_fn = plotters[exp_num]
        csv_path = os.path.join(args.results_dir, csv_name)
        png_path = os.path.join(args.results_dir, png_name)
        if not os.path.exists(csv_path):
            print(f"Brak: {csv_path}  (najpierw uruchom odpowiedni eksperyment)")
            continue
        plot_fn(csv_path, png_path)


if __name__ == "__main__":
    main()
