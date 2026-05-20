"""Uniform random bot."""

import random

from cops_and_robbers.bots.bot_base import BotBase
from cops_and_robbers.core.game_state import GameState
from cops_and_robbers.core.player import PlayerRole


class RandomBot(BotBase):
    def __init__(self, role: PlayerRole, seed: int | None = None):
        super().__init__(role)
        self._rng = random.Random(seed)

    def choose_move(self, state: GameState, legal_moves: list[int]) -> int:
        if not legal_moves:
            raise ValueError("legal_moves must not be empty")
        return self._rng.choice(legal_moves)
