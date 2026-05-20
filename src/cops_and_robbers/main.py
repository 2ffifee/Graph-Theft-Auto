"""Application entry point."""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Play Graph Theft Auto.")
    parser.add_argument("--n", type=int, default=10, help="number of vertices")
    parser.add_argument("--m", type=int, default=15, help="number of edges")
    parser.add_argument("--rounds", type=int, default=20, help="round limit")
    parser.add_argument("--seed", type=int, default=None, help="random seed")
    parser.add_argument(
        "--start",
        action="store_true",
        help="skip the setup screen and go directly to starting-position selection",
    )
    args = parser.parse_args()

    from cops_and_robbers.ui.app import CopsAndRobbersApp

    app = CopsAndRobbersApp(
        initial_n=args.n,
        initial_m=args.m,
        initial_rounds=args.rounds,
        seed=args.seed,
        start_immediately=args.start,
    )
    app.run()


if __name__ == "__main__":
    main()
