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


@dataclass(init=False)
class GameState:
    graph: GraphModel
    cop_positions: tuple[int, ...]
    robber_position: int
    round_limit: int
    current_player: PlayerRole = PlayerRole.COP
    current_round: int = 1
    status: GameStatus = GameStatus.PLAYING
    move_history: list[MoveRecord] = field(default_factory=list)

    def __init__(
        self,
        graph: GraphModel,
        robber_position: int,
        round_limit: int,
        cop_position: int | None = None,
        cop_positions: tuple[int, ...] | list[int] | None = None,
        current_player: PlayerRole = PlayerRole.COP,
        current_round: int = 1,
        status: GameStatus = GameStatus.PLAYING,
        move_history: list[MoveRecord] | None = None,
    ):
        if cop_positions is None:
            if cop_position is None:
                raise ValueError("either cop_position or cop_positions must be provided")
            normalized_cop_positions = (cop_position,)
        else:
            if cop_position is not None:
                raise ValueError("provide either cop_position or cop_positions, not both")
            normalized_cop_positions = tuple(cop_positions)

        if not normalized_cop_positions:
            raise ValueError("at least one cop position is required")

        self.graph = graph
        self.cop_positions = normalized_cop_positions
        self.robber_position = robber_position
        self.round_limit = round_limit
        self.current_player = current_player
        self.current_round = current_round
        self.status = status
        self.move_history = list(move_history) if move_history is not None else []

    @property
    def cop_position(self) -> int:
        """Compatibility helper for the current one-cop UI and bots."""
        return self.cop_positions[0]

    @cop_position.setter
    def cop_position(self, value: int) -> None:
        self.cop_positions = (value, *self.cop_positions[1:])

    @property
    def cop_count(self) -> int:
        return len(self.cop_positions)

    def current_position(self) -> int:
        if self.current_player is PlayerRole.COP:
            return self.cop_position
        return self.robber_position

    def clone(self, include_history: bool = True) -> "GameState":
        return GameState(
            graph=self.graph,
            cop_positions=self.cop_positions,
            robber_position=self.robber_position,
            round_limit=self.round_limit,
            current_player=self.current_player,
            current_round=self.current_round,
            status=self.status,
            move_history=list(self.move_history) if include_history else [],
        )
