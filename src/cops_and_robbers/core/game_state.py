"""Mutable game state for a single play session."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from cops_and_robbers.core.graph_model import GraphModel
from cops_and_robbers.core.move import MoveRecord
from cops_and_robbers.core.player import PlayerRole


class GameStatus(Enum):
    SETUP = "setup"
    PLAYING = "playing"
    COP_WIN = "cop_win"
    ROBBER_WIN = "robber_win"

    @property
    def label(self) -> str:
        labels = {
            GameStatus.SETUP: "Setup",
            GameStatus.PLAYING: "Playing",
            GameStatus.COP_WIN: "Cop wins",
            GameStatus.ROBBER_WIN: "Robber wins",
        }
        return labels[self]


@dataclass
class GameState:
    graph: GraphModel
    cop_position: int
    robber_position: int
    round_limit: int
    current_player: PlayerRole = PlayerRole.COP
    current_round: int = 1
    status: GameStatus = GameStatus.PLAYING
    move_history: list[MoveRecord] = field(default_factory=list)

    def current_position(self) -> int:
        if self.current_player is PlayerRole.COP:
            return self.cop_position
        return self.robber_position

    def clone(self) -> "GameState":
        return GameState(
            graph=self.graph,
            cop_position=self.cop_position,
            robber_position=self.robber_position,
            round_limit=self.round_limit,
            current_player=self.current_player,
            current_round=self.current_round,
            status=self.status,
            move_history=list(self.move_history),
        )
