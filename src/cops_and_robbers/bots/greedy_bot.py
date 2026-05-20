"""Greedy distance-based bot."""

import random

from cops_and_robbers.bots.bot_base import BotBase
from cops_and_robbers.core.game_state import GameState
from cops_and_robbers.core.player import PlayerRole


class GreedyBot(BotBase):
    def __init__(self, role: PlayerRole, seed: int | None = None):
        super().__init__(role)
        self._rng = random.Random(seed)

    def choose_move(self, state: GameState, legal_moves: list[int]) -> int:
        if not legal_moves:
            raise ValueError("legal_moves must not be empty")

        if self.role is PlayerRole.COP:
            scores = {
                move: state.graph.shortest_distance(move, state.robber_position)
                for move in legal_moves
            }
            best_score = min(scores.values())
        else:
            scores = {
                move: state.graph.shortest_distance(move, state.cop_position)
                for move in legal_moves
            }
            best_score = max(scores.values())

        best_moves = [move for move, score in scores.items() if score == best_score]
        return self._rng.choice(best_moves)
