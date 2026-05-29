# Graph Theft Auto

A minimal playable desktop implementation of a Cops and Robbers game on finite graphs.

The application uses Python, Pygame, and NetworkX. Version 1 supports one to three cops, one robber, random connected graphs, a round limit, click-based player-vs-player gameplay, and a clean code layout for later graph theory extensions.

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

## Current Features

- Setup screen with controls for vertices `n`, edges `m`, round limit `T`, and number of cops.
- Mode selection for Player vs Player, Player Cop vs Bot Robber, Bot Cop vs Player Robber, and Bot vs Bot.
- Bot selection between Random and Greedy.
- Validation for `3 <= n <= 30`, `n - 1 <= m <= n(n - 1)/2`, and `1 <= T <= 200`.
- Connected random graph generation with exact edge count.
- Manual starting-position selection: cops first, robber second.
- Staged multi-cop turns for player-vs-player games.
- Clickable legal move highlights.
- Restart current graph and choose new starting positions.
- Generate a new graph with the same setup values.
- Keyboard shortcuts: `R` restarts positions, `N` generates a new graph, `Esc` quits.
- Random and greedy bots with multi-cop move support.

## Graph Generation

The random connected graph generator first creates a random spanning tree and then adds random extra edges until the requested number of edges is reached. This guarantees connectedness and exact edge count, but it is not a uniform sampler over all connected graphs with n vertices and m edges.

## Planned Extensions

- Named graph families such as paths, cycles, grids, ladders, trees, and complete graphs.
- Minimax and optimal finite-horizon bots.
- Cop-win detection and dismantling analysis.
- Custom graph editor.
