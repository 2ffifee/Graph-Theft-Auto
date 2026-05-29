"""Base class for non-UI bot strategies."""

from abc import ABC, abstractmethod

from cops_and_robbers.core.game_state import GameState
from cops_and_robbers.core.move import Move
from cops_and_robbers.core.player import PlayerRole


class BotBase(ABC):
    def __init__(self, role: PlayerRole):
        self.role = role

    @abstractmethod
    def choose_move(self, state: GameState, legal_moves: list[int] | list[Move]) -> int | Move:
        raise NotImplementedError
