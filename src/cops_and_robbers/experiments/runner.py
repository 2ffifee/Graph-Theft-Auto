"""Headless game simulation: bot factories, placement, single-game and batch runners.

This module has no pygame / UI dependencies; it can be used from any script
or notebook to run large batches of bot-vs-bot games and collect statistics.

Typical usage::

    from cops_and_robbers.experiments.runner import (
        BotSpec, simulate_batch,
    )

    rows = simulate_batch(
        n=12, m=18, T=30, n_cops=1,
        cop_spec=BotSpec("greedy"),
        robber_spec=BotSpec("minimax", depth=3),
        n_games=200, master_seed=42, graph_type="any",
    )
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from multiprocessing import Pool
from typing import Iterable, Iterator

from cops_and_robbers.bots.bot_base import BotBase
from cops_and_robbers.bots.greedy_bot import GreedyBot
from cops_and_robbers.bots.minimax_bot import AdaptiveMinimaxBot, MinimaxBot
from cops_and_robbers.bots.random_bot import RandomBot
from cops_and_robbers.core.game_rules import GameRules
from cops_and_robbers.core.game_state import GameState, GameStatus
from cops_and_robbers.core.graph_model import GraphModel
from cops_and_robbers.core.player import PlayerRole
from cops_and_robbers.core.graph_generator import generate_connected_graph
from cops_and_robbers.utils.validation import (
    GRAPH_TYPE_ANY,
    GRAPH_TYPE_PLANAR,
    GRAPH_TYPE_TREE,
    edge_bounds_for_graph_type,
)


# ============================================================================
# Bot specification & factory
# ============================================================================

@dataclass(frozen=True)
class BotSpec:
    """Declarative description of a bot.

    `kind` is one of "random", "greedy", "minimax", "adaptive_minimax".
    `depth` is required for minimax, ignored otherwise.
    """
    kind: str
    depth: int | None = None

    def label(self) -> str:
        if self.kind == "minimax":
            return f"minimax(d={self.depth})"
        if self.kind == "adaptive_minimax":
            return f"minimax(d={self.depth},adaptive)"
        return self.kind

    def __str__(self) -> str:
        return self.label()


def make_bot(spec: BotSpec, role: PlayerRole, seed: int | None) -> BotBase:
    """Construct a bot of the given kind/role from a spec."""
    if spec.kind == "random":
        return RandomBot(role=role, seed=seed)
    if spec.kind == "greedy":
        return GreedyBot(role=role, seed=seed)
    if spec.kind == "minimax":
        if spec.depth is None or spec.depth < 1:
            raise ValueError(f"minimax bot requires depth >= 1; got {spec.depth!r}")
        return MinimaxBot(role=role, depth=spec.depth, seed=seed)
    if spec.kind == "adaptive_minimax":
        if spec.depth is None or spec.depth < 1:
            raise ValueError(f"adaptive minimax bot requires depth >= 1; got {spec.depth!r}")
        return AdaptiveMinimaxBot(role=role, depth=spec.depth, seed=seed)
    raise ValueError(f"unknown bot kind: {spec.kind!r}")


# ============================================================================
# Starting position selection
# ============================================================================

def place_random(
    graph: GraphModel, n_cops: int, rng: random.Random
) -> tuple[tuple[int, ...], int]:
    """Pick `n_cops` cop positions and a distinct robber position uniformly at random."""
    vertices = list(graph.vertices())
    if len(vertices) < n_cops + 1:
        raise ValueError(
            f"graph has {len(vertices)} vertices; need at least {n_cops + 1}"
        )
    picks = rng.sample(vertices, n_cops + 1)
    return tuple(picks[:n_cops]), picks[n_cops]


def place_heuristic(
    graph: GraphModel, n_cops: int, rng: random.Random
) -> tuple[tuple[int, ...], int]:
    """Heuristic placement matching the in-app bot start logic.

    Cops: choose vertices with minimum eccentricity (tie-break: higher degree).
    Robber: choose vertex maximizing min-distance to chosen cops (tie-break: higher degree).
    Ties broken by deterministic RNG choice.
    """
    nx_g = graph.to_networkx()
    vertices = list(graph.vertices())

    # Eccentricity = max distance to any other vertex
    eccentricities: dict[int, int] = {}
    distances: dict[int, dict[int, int]] = {}
    for v in vertices:
        from networkx import single_source_shortest_path_length
        dist = dict(single_source_shortest_path_length(nx_g, v))
        distances[v] = dist
        eccentricities[v] = max(dist.values()) if dist else 0

    degrees = {v: nx_g.degree(v) for v in vertices}

    # Cops: pick top n_cops by (+ecc, -deg) to minimize, with random tie-break.
    # This mirrors CopsAndRobbersApp._choose_bot_cop_start.
    def cop_key(v: int) -> tuple[int, int]:
        return (eccentricities[v], -degrees[v])

    sorted_for_cops = sorted(vertices, key=cop_key)
    # Group by key for random tie-break
    cops: list[int] = []
    i = 0
    while len(cops) < n_cops and i < len(sorted_for_cops):
        # Find run of equal keys
        key = cop_key(sorted_for_cops[i])
        run = [v for v in sorted_for_cops[i:] if cop_key(v) == key]
        rng.shuffle(run)
        for v in run:
            if v not in cops and len(cops) < n_cops:
                cops.append(v)
        i += len(run)
    cop_tuple = tuple(cops)

    # Robber: maximize min-dist to cops, then maximize degree
    def robber_key(v: int) -> tuple[int, int]:
        if v in cop_tuple:
            return (-1, -1)  # exclude
        min_d = min(distances[c].get(v, 10**9) for c in cop_tuple)
        return (-min_d, -degrees[v])  # min in this key = best (we minimize)

    candidates = [v for v in vertices if v not in cop_tuple]
    if not candidates:
        raise ValueError("no robber-eligible vertex left")
    sorted_for_robber = sorted(candidates, key=robber_key)
    best_key = robber_key(sorted_for_robber[0])
    best_robbers = [v for v in sorted_for_robber if robber_key(v) == best_key]
    robber = rng.choice(best_robbers)

    return cop_tuple, robber


PlacementFn = callable  # type alias — (graph, n_cops, rng) -> (cops, robber)


def get_placement_fn(name: str) -> PlacementFn:
    if name == "random":
        return place_random
    if name == "heuristic":
        return place_heuristic
    raise ValueError(f"unknown placement: {name!r}")


# ============================================================================
# Single game
# ============================================================================

@dataclass
class GameResult:
    cop_wins: bool
    rounds_played: int
    moves_played: int
    elapsed_seconds: float
    initial_cops: tuple[int, ...]
    initial_robber: int


def simulate_game(
    graph: GraphModel,
    *,
    n_cops: int,
    T: int,
    cop_spec: BotSpec,
    robber_spec: BotSpec,
    seed: int,
    placement: str = "heuristic",
    max_moves_safety: int | None = None,
) -> GameResult:
    """Play one game to completion.

    The bot seeds are derived from `seed` so a single master seed makes the
    whole game reproducible.
    """
    placement_rng = random.Random(seed * 1_000_003 + 1)
    cop_seed = seed * 7 + 11
    robber_seed = seed * 13 + 17

    place_fn = get_placement_fn(placement)
    cop_positions, robber_position = place_fn(graph, n_cops, placement_rng)

    state = GameState(
        graph=graph,
        cop_positions=cop_positions,
        robber_position=robber_position,
        round_limit=T,
    )
    rules = GameRules()
    cop_bot = make_bot(cop_spec, PlayerRole.COP, cop_seed)
    robber_bot = make_bot(robber_spec, PlayerRole.ROBBER, robber_seed)

    if max_moves_safety is None:
        # 2 moves per round + safety margin; never hit unless something is wrong
        max_moves_safety = T * 4 + 50

    moves = 0
    start_time = time.perf_counter()
    while state.status is GameStatus.PLAYING and moves < max_moves_safety:
        legal_moves = rules.get_legal_moves(state)
        if not legal_moves:
            break
        bot = cop_bot if state.current_player is PlayerRole.COP else robber_bot
        move = bot.choose_move(state, legal_moves)
        rules.apply_move(state, move)
        moves += 1
    elapsed = time.perf_counter() - start_time

    if state.status is GameStatus.PLAYING:
        # Safety exit — treat as draw favoring robber (lasted T rounds without capture)
        cop_wins = False
        rounds = T
    else:
        cop_wins = state.status is GameStatus.COP_WIN
        rounds = state.current_round if cop_wins else T

    return GameResult(
        cop_wins=cop_wins,
        rounds_played=rounds,
        moves_played=moves,
        elapsed_seconds=elapsed,
        initial_cops=cop_positions,
        initial_robber=robber_position,
    )


def _simulate_batch_game(
    task: tuple[int, int, int, int, BotSpec, BotSpec, int, str, str],
) -> GameResult:
    n, m, T, n_cops, cop_spec, robber_spec, game_seed, graph_type, placement = task
    graph = generate_connected_graph(n, m, seed=game_seed, graph_type=graph_type)
    return simulate_game(
        graph,
        n_cops=n_cops,
        T=T,
        cop_spec=cop_spec,
        robber_spec=robber_spec,
        seed=game_seed,
        placement=placement,
    )


# ============================================================================
# Batch
# ============================================================================

@dataclass
class BatchSummary:
    n: int
    m: int
    T: int
    n_cops: int
    graph_type: str
    cop_spec: BotSpec
    robber_spec: BotSpec
    n_games: int
    cop_wins: int
    robber_wins: int
    mean_rounds: float
    mean_seconds_per_game: float
    placement: str

    @property
    def win_rate(self) -> float:
        return self.cop_wins / self.n_games if self.n_games else 0.0

    def as_dict(self) -> dict:
        return {
            "n": self.n,
            "m": self.m,
            "T": self.T,
            "n_cops": self.n_cops,
            "graph_type": self.graph_type,
            "cop_strategy": str(self.cop_spec),
            "robber_strategy": str(self.robber_spec),
            "n_games": self.n_games,
            "cop_wins": self.cop_wins,
            "robber_wins": self.robber_wins,
            "win_rate": round(self.win_rate, 4),
            "mean_rounds": round(self.mean_rounds, 2),
            "mean_seconds_per_game": round(self.mean_seconds_per_game, 4),
            "placement": self.placement,
        }


def simulate_batch(
    *,
    n: int,
    m: int,
    T: int,
    n_cops: int,
    cop_spec: BotSpec,
    robber_spec: BotSpec,
    n_games: int,
    master_seed: int = 42,
    graph_type: str = GRAPH_TYPE_ANY,
    placement: str = "heuristic",
    progress: bool = True,
    progress_prefix: str = "",
    workers: int = 1,
) -> BatchSummary:
    """Run `n_games` games. Each game uses a freshly generated graph + new seed."""
    cop_wins = 0
    total_rounds = 0
    total_seconds = 0.0
    start = time.perf_counter()
    workers = max(1, workers)

    tasks = [
        (
            n, m, T, n_cops, cop_spec, robber_spec,
            master_seed * 1_000_003 + i * 31 + 1,
            graph_type, placement,
        )
        for i in range(n_games)
    ]

    if workers == 1:
        results_iter: Iterable[GameResult] = (_simulate_batch_game(task) for task in tasks)
    else:
        chunksize = max(1, n_games // (workers * 4))
        pool = Pool(processes=workers)
        results_iter = pool.imap_unordered(_simulate_batch_game, tasks, chunksize=chunksize)

    try:
        for i, result in enumerate(results_iter, start=1):
            if result.cop_wins:
                cop_wins += 1
            total_rounds += result.rounds_played
            total_seconds += result.elapsed_seconds

            if progress and i % max(1, n_games // 10) == 0:
                elapsed = time.perf_counter() - start
                rate = i / elapsed if elapsed > 0 else 0
                print(
                    f"  {progress_prefix}"
                    f"{i}/{n_games} games  "
                    f"cop_wins={cop_wins} ({cop_wins/i:.1%})  "
                    f"{rate:.1f} g/s",
                    flush=True,
                )
    finally:
        if workers != 1:
            pool.close()
            pool.join()

    return BatchSummary(
        n=n, m=m, T=T, n_cops=n_cops, graph_type=graph_type,
        cop_spec=cop_spec, robber_spec=robber_spec,
        n_games=n_games,
        cop_wins=cop_wins,
        robber_wins=n_games - cop_wins,
        mean_rounds=total_rounds / n_games if n_games else 0.0,
        mean_seconds_per_game=total_seconds / n_games if n_games else 0.0,
        placement=placement,
    )


# ============================================================================
# CSV writing
# ============================================================================

def write_csv(path: str, rows: Iterable[dict], fieldnames: list[str] | None = None) -> None:
    """Write a list of dict rows to a CSV file."""
    import csv
    import os
    rows = list(rows)
    if not rows:
        raise ValueError("no rows to write")
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def clamp_edge_count(n: int, m: int, graph_type: str = GRAPH_TYPE_ANY) -> int:
    """Adjust `m` to the valid range for given n and graph type."""
    if graph_type == GRAPH_TYPE_TREE:
        return n - 1
    lo, hi = edge_bounds_for_graph_type(n, graph_type)
    return max(lo, min(hi, m))


# Re-export common constants for convenience
__all__ = [
    "BotSpec", "GameResult", "BatchSummary",
    "make_bot", "simulate_game", "simulate_batch",
    "place_random", "place_heuristic",
    "write_csv", "clamp_edge_count",
    "GRAPH_TYPE_ANY", "GRAPH_TYPE_TREE", "GRAPH_TYPE_PLANAR",
]
