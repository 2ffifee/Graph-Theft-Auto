"""Greedy distance-based bot."""

import random

from cops_and_robbers.bots.bot_base import BotBase
from cops_and_robbers.core.game_state import GameState
from cops_and_robbers.core.move import Move
from cops_and_robbers.core.player import PlayerRole


class GreedyBot(BotBase):
    def __init__(self, role: PlayerRole, seed: int | None = None):
        super().__init__(role)
        self._rng = random.Random(seed)

    def choose_move(self, state: GameState, legal_moves: list[int] | list[Move]) -> int | Move:
        if not legal_moves:
            raise ValueError("legal_moves must not be empty")

        if self.role is PlayerRole.COP:
            if isinstance(legal_moves[0], Move):
                return self._choose_multi_cop_move(state, legal_moves)
            scores = {
                move: state.graph.shortest_distance(move, state.robber_position)
                for move in legal_moves
                if isinstance(move, int)
            }
            best_score = min(scores.values())
        else:
            scores = {
                move: min(
                    state.graph.shortest_distance(move, cop_position)
                    for cop_position in state.cop_positions
                )
                for move in legal_moves
                if isinstance(move, int)
            }
            best_score = max(scores.values())

        best_moves = [move for move, score in scores.items() if score == best_score]
        return self._rng.choice(best_moves)

    def _choose_multi_cop_move(self, state: GameState, legal_moves: list[int] | list[Move]) -> Move:
        scored_moves: dict[Move, tuple[int, int, int]] = {}
        for move in legal_moves:
            if not isinstance(move, Move):
                continue
            distances = [
                state.graph.shortest_distance(destination, state.robber_position)
                for destination in move.destinations
            ]
            min_distance = min(distances)
            total_distance = sum(distances)
            duplicate_penalty = len(move.destinations) - len(set(move.destinations))
            scored_moves[move] = (min_distance, total_distance, duplicate_penalty)

        best_score = min(scored_moves.values())
        best_moves = [move for move, score in scored_moves.items() if score == best_score]
        return self._rng.choice(best_moves)
