# Experiments

[Polish version](README.md)

This directory contains scripts for running experiments without the Pygame
interface. Each experiment simulates many bot-vs-bot games and saves the
results to CSV, while `plot_results.py` generates PNG charts from those files.

The experiments use the same game model as the application: the graph is
undirected, the cops move first, and each round consists of one joint cop move
followed by one robber move. A capture occurs whenever a cop and the robber
occupy the same vertex after a move.

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

Plot generation requires `matplotlib`, which is included in
`requirements.txt`.

## Shared Assumptions

- The default starting-position strategy is `placement=heuristic`, not random
  placement.
- Cops start on central vertices with minimum eccentricity; higher degree is
  preferred when scores are tied.
- The robber starts on a vertex that maximizes its distance from the nearest
  cop; higher degree is preferred when scores are tied.
- `random` placement remains available, but is not used by the main
  experiments.
- Every game receives a fresh graph and independent random seeds derived from
  `--seed`.
- The `any` generator is not a uniform sampler over all connected graphs. It
  creates a random spanning tree first and then adds random edges.
- The `tree` generator creates a random tree.
- The `planar` generator starts with a tree and only adds edges that preserve
  planarity.

## Experiment 2: Bot-vs-Bot Matrix

Run with:

```bash
python -m cops_and_robbers.experiments.exp2_bot_matrix
```

The goal is to compare cop and robber movement strategies while using the same
starting-position heuristic.

Compared strategies:

```text
cop:    random, greedy, minimax(d=3)
robber: random, greedy, minimax(d=3)
```

Each strategy pair is tested independently, for example a `greedy` cop against
a `minimax(d=3)` robber.

Default configuration:

```text
number of cops: 1
graph type: any
games: 100 per matrix cell and graph bucket
placement: heuristic
round limit: T=max(20, round(5n/3))
```

Graph buckets:

```text
n12_sparse: n=12, m=18, T=20
n12_dense:  n=12, m=30, T=20
n30_sparse: n=30, m=45, T=50
n30_dense:  n=30, m=75, T=50
```

CSV output:

```text
src/results/exp2_bot_matrix.csv
```

A separate PNG chart is generated for each graph bucket:

```text
src/results/exp2_bot_matrix_n12_sparse.png
src/results/exp2_bot_matrix_n12_dense.png
src/results/exp2_bot_matrix_n30_sparse.png
src/results/exp2_bot_matrix_n30_dense.png
```

The result shows how often the cop wins against a particular robber strategy
on random graphs from each bucket. It is an empirical comparison rather than a
proof of optimality; the minimax search is depth-limited.

## Experiment 3: Effect of Graph Size

Run with:

```bash
python -m cops_and_robbers.experiments.exp3_size_sweep
```

The goal is to measure how cop-strategy effectiveness changes as the graph
grows.

Default configuration:

```text
n: 5, 8, 10, 15, 20, 25, 30
m: round(1.5n), clamped to the valid range
T: max(10, 2n)
number of cops: 1
graph type: any
games: 100 per data point
placement: heuristic
```

By default, the experiment compares three cop strategies:

```text
random
greedy
minimax(d=3)
```

against two robber variants:

```text
greedy
minimax(d=3)
```

This produces two sets of curves:

```text
random/greedy/minimax cops vs. a greedy robber
random/greedy/minimax cops vs. a minimax(d=3) robber
```

CSV output:

```text
src/results/exp3_size_sweep.csv
```

By default, the plotting script generates views grouped both by fixed robber
strategy and by fixed cop strategy:

```text
src/results/exp3_size_sweep_robber_greedy.png
src/results/exp3_size_sweep_robber_minimax.png
src/results/exp3_size_sweep_cop_random.png
src/results/exp3_size_sweep_cop_greedy.png
src/results/exp3_size_sweep_cop_minimax.png
```

The experiment shows whether a strategy loses effectiveness as graph size
increases. Separate charts make it possible to distinguish performance against
weaker and stronger opponents.

## Experiment 4: Number of Cops and Graph Type

Run with:

```bash
python -m cops_and_robbers.experiments.exp4_cops_x_type
```

The goal is to measure how the number of cops affects the outcome on different
types of graphs.

Compared values:

```text
number of cops k: 1, 2, 3
graph types: any, tree, planar
```

Default configuration:

```text
cop bot: minimax(d=3, adaptive)
robber bot: minimax(d=3, adaptive)
games: 20 per configuration
placement: heuristic
round limit: T=max(20, round(5n/3))
```

Graph buckets:

```text
n12_sparse: n=12, m=18, T=20
n12_dense:  n=12, m=30, T=20
n30_sparse: n=30, m=45, T=50
n30_dense:  n=30, m=75, T=50
```

Trees automatically use exactly `n-1` edges. Planar graphs are restricted by
the planar edge limit `3n-6`.

Adaptive minimax depth:

```text
root branching <= 50  -> depth 3
51..350               -> depth 2
>350                  -> depth 1
```

This is especially important with multiple cops because the number of joint
cop moves is the product of the legal-move counts of the individual cops.

CSV output:

```text
src/results/exp4_cops_x_type.csv
```

PNG output:

```text
src/results/exp4_cops_x_type.png
```

This experiment is an empirical evaluation of the bots, not a proof of a
graph-theoretic result. Trees are expected to have a very high cop win rate
already for `k=1`. The Aigner-Fromme theorem states that three cops suffice on
planar graphs under optimal play, while this project uses depth-limited
minimax.

## Running the Full Suite

Run all experiments and generate their charts with:

```bash
python scripts/run_full_experiments.py --workers 4
```

Default outputs:

```text
CSV and PNG: src/results/
log:         src/results/full_experiments.log
```

For a lighter run:

```bash
python scripts/run_full_experiments.py --workers 4 --exp2-games 50 --exp3-games 50 --exp4-games 10
```

## Runtime Benchmark

Before starting the full suite, run representative samples of its slowest
configurations with:

```bash
python scripts/benchmark_experiments.py --workers 4
```

By default, the benchmark saves its output and log to:

```text
tmp_bench/
```

## Regenerating Charts Only

If the CSV files already exist, regenerate only the PNG charts with:

```bash
python -m cops_and_robbers.experiments.plot_results --results-dir src/results --exp 2 3 4
```

This does not rerun the simulations.

## Main CSV Columns

```text
n, m, T
n_cops
graph_type
cop_strategy
robber_strategy
n_games
cop_wins
robber_wins
win_rate
mean_rounds
mean_seconds_per_game
placement
bucket
```

Experiment 4 also records a `k` column equal to the number of cops.

## Using the Runner from Python

`runner.py` can be imported from a notebook or another script:

```python
from cops_and_robbers.experiments.runner import BotSpec, simulate_batch

summary = simulate_batch(
    n=15,
    m=22,
    T=30,
    n_cops=2,
    cop_spec=BotSpec("minimax", depth=3),
    robber_spec=BotSpec("greedy"),
    n_games=500,
    master_seed=2025,
    graph_type="planar",
    placement="heuristic",
)
print(summary.as_dict())
```
