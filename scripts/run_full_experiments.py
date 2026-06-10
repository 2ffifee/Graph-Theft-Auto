"""Run the full experiment suite and generate plots.

The script runs experiments 2, 3, and 4 sequentially, then generates PNG plots
from the CSV outputs. It logs command output and elapsed time for each step.
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
    parser = argparse.ArgumentParser(description="Run full experiments and generate plots.")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    parser.add_argument("--output-dir", default="src/results")
    parser.add_argument("--log-file", default=None)
    parser.add_argument("--exp2-games", type=int, default=100)
    parser.add_argument("--exp3-games", type=int, default=100)
    parser.add_argument("--exp4-games", type=int, default=20)
    parser.add_argument("--skip-exp2", action="store_true")
    parser.add_argument("--skip-exp3", action="store_true")
    parser.add_argument("--skip-exp4", action="store_true")
    parser.add_argument("--skip-plots", action="store_true")
    parser.add_argument("--with-pytest", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file = Path(args.log_file) if args.log_file else output_dir / "full_experiments.log"
    log_file.write_text(
        "Full experiment run log\n"
        f"workers={args.workers}\n"
        f"output_dir={output_dir}\n"
        f"exp2_games={args.exp2_games}\n"
        f"exp3_games={args.exp3_games}\n"
        f"exp4_games={args.exp4_games}\n",
        encoding="utf-8",
    )

    python = sys.executable
    commands: list[tuple[str, list[str]]] = []
    if args.with_pytest:
        commands.append(("pytest", [python, "-m", "pytest"]))
    if not args.skip_exp2:
        commands.append(
            (
                "exp2_bot_matrix",
                [
                    python,
                    "-m",
                    "cops_and_robbers.experiments.exp2_bot_matrix",
                    "--games",
                    str(args.exp2_games),
                    "--output-dir",
                    str(output_dir),
                    "--workers",
                    str(args.workers),
                    "--quiet",
                ],
            )
        )
    if not args.skip_exp3:
        commands.append(
            (
                "exp3_size_sweep",
                [
                    python,
                    "-m",
                    "cops_and_robbers.experiments.exp3_size_sweep",
                    "--games",
                    str(args.exp3_games),
                    "--output-dir",
                    str(output_dir),
                    "--workers",
                    str(args.workers),
                    "--quiet",
                ],
            )
        )
    if not args.skip_exp4:
        commands.append(
            (
                "exp4_cops_x_type",
                [
                    python,
                    "-m",
                    "cops_and_robbers.experiments.exp4_cops_x_type",
                    "--games",
                    str(args.exp4_games),
                    "--output-dir",
                    str(output_dir),
                    "--workers",
                    str(args.workers),
                    "--quiet",
                ],
            )
        )
    if not args.skip_plots:
        exp_numbers: list[str] = []
        if not args.skip_exp2:
            exp_numbers.append("2")
        if not args.skip_exp3:
            exp_numbers.append("3")
        if not args.skip_exp4:
            exp_numbers.append("4")
        if exp_numbers:
            commands.append(
                (
                    "plot_results",
                    [
                        python,
                        "-m",
                        "cops_and_robbers.experiments.plot_results",
                        "--results-dir",
                        str(output_dir),
                        "--exp",
                        *exp_numbers,
                    ],
                )
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
    print(f"CSV/PNG output: {output_dir}")
    print(f"Log file: {log_file}")


if __name__ == "__main__":
    main()
