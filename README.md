# Graph Theft Auto

An interactive desktop implementation of the classic Cops and Robbers game on
finite graphs. It combines a playable Pygame interface with reusable game logic,
several bot strategies, and a headless simulation framework for comparing them.

Built with Python 3.11+, Pygame, NetworkX, and Matplotlib.

## Highlights

- Play with one to three cops in player-vs-player, player-vs-bot, or bot-vs-bot modes.
- Generate connected general, tree, and planar graphs with configurable sizes.
- Compare random, greedy, and depth-limited minimax bots with alpha-beta pruning.
- Run reproducible experiments without the UI and export results to CSV and PNG.
- Keep the game rules, graph model, bots, experiments, and rendering code separated.

## Rules

- The game is played on a connected simple undirected graph.
- There are one to three cops and one robber.
- The cop moves first.
- On the cops' turn, each cop may move to an adjacent vertex or stay on the current vertex.
- If any cop and the robber occupy the same vertex after any move, the cops win.
- A full round is one joint cops' move followed by one robber move.
- If the robber survives through the robber turn of the final round, the robber wins.
- At the start of each game, cops choose starting vertices first, then the robber chooses a different starting vertex.

## Setup on Linux

Requires Python 3.11 or newer with `venv` support. On Debian/Ubuntu, install
the system prerequisite if it is not already available:

```bash
sudo apt install python3-venv
```

Some releases use a versioned package such as `python3.12-venv` instead.

```bash
./scripts/setup_linux.sh
./scripts/run_linux.sh
```

## Setup on Windows PowerShell

```powershell
.\scripts\setup_windows.ps1
.\scripts\run_windows.ps1
```

If PowerShell refuses to run scripts, allow local scripts for the current user:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Manual Setup

```bash
python -m venv .venv
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
python -m cops_and_robbers.main
```

## Running Tests

```bash
pytest
```

The test suite covers graph generation, game rules and state transitions,
multi-cop gameplay, bot decisions, placement heuristics, and UI integration.

## Current Features

- Setup screen with controls for vertices `n`, edges `m`, round limit `T`, and number of cops.
- Mode selection for Player vs Player, Player Cop vs Bot Robber, Bot Cop vs Player Robber, and Bot vs Bot.
- Bot level selection from `1 Random` through `5 Expert`.
- Higher bot levels use adaptive minimax depth based on graph complexity and number of cops.
- Validation for `3 <= n <= 30`, `n - 1 <= m <= n(n - 1)/2`, and `1 <= T <= 200`.
- Connected random graph generation with exact edge count.
- Manual starting-position selection: cops first, robber second.
- Staged multi-cop turns for player-vs-player games.
- Clickable legal move highlights.
- Restart current graph and choose new starting positions.
- Generate a new graph with the same setup values.
- Keyboard shortcuts: `R` restarts positions, `N` generates a new graph, `Esc` quits.
- Random, greedy, and alpha-beta minimax bots with multi-cop move support.

## Graph Generation

The random connected graph generator first creates a random spanning tree and then adds random extra edges until the requested number of edges is reached. This guarantees connectedness and exact edge count, but it is not a uniform sampler over all connected graphs with n vertices and m edges.

## Experiments

The headless experiment suite runs batches of bot-vs-bot games across different
graph sizes, densities, graph types, and numbers of cops. Runs are seeded for
reproducibility and can use multiple worker processes.

```bash
python scripts/run_full_experiments.py --workers 4
```

See the [experiment documentation](src/cops_and_robbers/experiments/README.en.md)
for configurations, output formats, and interpretation of the included results.

## Project Structure

```text
src/cops_and_robbers/
├── core/         graph model, game state, and rules
├── bots/         random, greedy, and minimax strategies
├── ui/           Pygame application and rendering
├── experiments/  headless simulations and plotting
└── utils/        validation and shared helpers
tests/             automated test suite
scripts/           setup, launch, and experiment commands
```
