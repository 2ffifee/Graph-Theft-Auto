"""Run small experiment benchmarks and log elapsed time for each command.

This script is intentionally separate from the experiment modules. It runs a
small, representative subset of the slow experiments so runtime can be estimated
before launching full CSV generation.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


def run_command(name: str, command: list[str], log_file: Path) -> float:
    start = time.perf_counter()
    header = f"\n=== {name} ===\n$ {' '.join(command)}\n"
    print(header, end="")
    with log_file.open("a", encoding="utf-8") as log:
        log.write(header)
        log.flush()
        completed = subprocess.run(
            command,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        elapsed = time.perf_counter() - start
        footer = f"\n[{name}] exit_code={completed.returncode} elapsed={elapsed:.1f}s\n"
        log.write(footer)
    print(f"[{name}] elapsed={elapsed:.1f}s exit_code={completed.returncode}")
    if completed.returncode != 0:
        raise SystemExit(f"{name} failed; see {log_file}")
    return elapsed


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark representative experiment subsets.")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    parser.add_argument("--output-dir", default="tmp_bench")
    parser.add_argument("--log-file", default=None)
    parser.add_argument("--exp2-games", type=int, default=5)
    parser.add_argument("--exp3-games", type=int, default=5)
    parser.add_argument("--exp4-games", type=int, default=3)
    parser.add_argument("--with-pytest", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file = Path(args.log_file) if args.log_file else output_dir / "benchmark_experiments.log"
    log_file.write_text(
        "Experiment benchmark log\n"
        f"workers={args.workers}\n"
        f"output_dir={output_dir}\n",
        encoding="utf-8",
    )

    python = sys.executable
    commands: list[tuple[str, list[str]]] = []
    if args.with_pytest:
        commands.append(("pytest", [python, "-m", "pytest"]))

    commands.extend(
        [
            (
                "exp2_n30_dense",
                [
                    python,
                    "-m",
                    "cops_and_robbers.experiments.exp2_bot_matrix",
                    "--games",
                    str(args.exp2_games),
                    "--buckets",
                    "n30_dense",
                    "--output-dir",
                    str(output_dir),
                    "--workers",
                    str(args.workers),
                    "--quiet",
                ],
            ),
            (
                "exp3_n5_n30",
                [
                    python,
                    "-m",
                    "cops_and_robbers.experiments.exp3_size_sweep",
                    "--games",
                    str(args.exp3_games),
                    "--n-values",
                    "5",
                    "30",
                    "--output-dir",
                    str(output_dir),
                    "--workers",
                    str(args.workers),
                    "--quiet",
                ],
            ),
            (
                "exp4_n30_dense_k1_k3_any_planar",
                [
                    python,
                    "-m",
                    "cops_and_robbers.experiments.exp4_cops_x_type",
                    "--games",
                    str(args.exp4_games),
                    "--buckets",
                    "n30_dense",
                    "--k-values",
                    "1",
                    "3",
                    "--graph-types",
                    "any",
                    "planar",
                    "--output-dir",
                    str(output_dir),
                    "--workers",
                    str(args.workers),
                    "--quiet",
                ],
            ),
        ]
    )

    total_start = time.perf_counter()
    timings: list[tuple[str, float]] = []
    for name, command in commands:
        elapsed = run_command(name, command, log_file)
        timings.append((name, elapsed))

    total_elapsed = time.perf_counter() - total_start
    summary_lines = ["\n=== SUMMARY ==="]
    summary_lines.extend(f"{name}: {elapsed:.1f}s" for name, elapsed in timings)
    summary_lines.append(f"total: {total_elapsed:.1f}s")
    summary = "\n".join(summary_lines) + "\n"
    with log_file.open("a", encoding="utf-8") as log:
        log.write(summary)
    print(summary)
    print(f"Log file: {log_file}")


if __name__ == "__main__":
    main()
