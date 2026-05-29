"""Rules for Cops and Robbers on graphs."""

from __future__ import annotations

from cops_and_robbers.core.game_state import GameState, GameStatus
from cops_and_robbers.core.move import MoveRecord
from cops_and_robbers.core.player import PlayerRole


class GameRules:
    def get_legal_moves(self, state: GameState) -> list[int]:
        if state.status is not GameStatus.PLAYING:
            return []
        return state.graph.legal_moves(state.current_position())

    def is_legal_move(self, state: GameState, destination: int) -> bool:
        return destination in self.get_legal_moves(state)

    def apply_move(self, state: GameState, destination: int) -> GameState:
        if state.status is not GameStatus.PLAYING:
            return state
        if not self.is_legal_move(state, destination):
            raise ValueError(f"illegal move to vertex {destination}")

        moved_player = state.current_player
        from_vertex = state.current_position()

        if moved_player is PlayerRole.COP:
            state.cop_position = destination
        else:
            state.robber_position = destination

        state.move_history.append(
            MoveRecord(
                player=moved_player,
                from_vertex=from_vertex,
                to_vertex=destination,
                round_number=state.current_round,
            )
        )

        if self.check_capture(state):
            state.status = GameStatus.COP_WIN
            return state

        if moved_player is PlayerRole.ROBBER:
            if state.current_round >= state.round_limit:
                state.status = GameStatus.ROBBER_WIN
            else:
                state.current_round += 1
                state.current_player = PlayerRole.COP
        else:
            state.current_player = PlayerRole.ROBBER

        return state

    def check_capture(self, state: GameState) -> bool:
        return state.robber_position in state.cop_positions

    def check_robber_survived(self, state: GameState) -> bool:
        return state.status is GameStatus.ROBBER_WIN
