"""Rules for Cops and Robbers on graphs."""

from __future__ import annotations

from itertools import product

from cops_and_robbers.core.game_state import GameState, GameStatus
from cops_and_robbers.core.move import Move, MoveRecord
from cops_and_robbers.core.player import PlayerRole


class GameRules:
    def get_legal_moves(self, state: GameState) -> list[int] | list[Move]:
        if state.status is not GameStatus.PLAYING:
            return []
        if state.current_player is PlayerRole.COP:
            if state.cop_count == 1:
                return self.get_legal_cop_destinations(state)
            return self.get_legal_cop_moves(state)
        return self.get_legal_robber_destinations(state)

    def get_legal_cop_destinations(self, state: GameState, cop_index: int = 0) -> list[int]:
        self._validate_cop_index(state, cop_index)
        if state.status is not GameStatus.PLAYING:
            return []
        return state.graph.legal_moves(state.cop_positions[cop_index])

    def get_legal_robber_destinations(self, state: GameState) -> list[int]:
        if state.status is not GameStatus.PLAYING:
            return []
        return state.graph.legal_moves(state.robber_position)

    def get_legal_cop_moves(self, state: GameState) -> list[Move]:
        if state.status is not GameStatus.PLAYING:
            return []
        per_cop_destinations = [
            state.graph.legal_moves(cop_position)
            for cop_position in state.cop_positions
        ]
        return [Move.cop(destinations) for destinations in product(*per_cop_destinations)]

    def get_legal_robber_moves(self, state: GameState) -> list[Move]:
        return [Move.robber(destination) for destination in self.get_legal_robber_destinations(state)]

    def is_legal_move(self, state: GameState, move: int | Move) -> bool:
        normalized_move = self._normalize_move(state, move)
        if normalized_move.player is PlayerRole.COP:
            return normalized_move in self.get_legal_cop_moves(state)
        return normalized_move in self.get_legal_robber_moves(state)

    def apply_move(self, state: GameState, move: int | Move) -> GameState:
        if state.status is not GameStatus.PLAYING:
            return state
        normalized_move = self._normalize_move(state, move)
        if not self.is_legal_move(state, normalized_move):
            raise ValueError(f"illegal move {normalized_move}")

        moved_player = normalized_move.player
        from_vertices = self._current_vertices_for_player(state, moved_player)

        if moved_player is PlayerRole.COP:
            state.cop_positions = normalized_move.destinations
        else:
            state.robber_position = normalized_move.destinations[0]

        state.move_history.append(
            MoveRecord(
                player=moved_player,
                from_vertices=from_vertices,
                to_vertices=normalized_move.destinations,
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

    def _normalize_move(self, state: GameState, move: int | Move) -> Move:
        if isinstance(move, Move):
            if move.player is not state.current_player:
                raise ValueError(f"expected {state.current_player.label} move, got {move.player.label}")
            expected_length = state.cop_count if move.player is PlayerRole.COP else 1
            if len(move.destinations) != expected_length:
                raise ValueError(
                    f"{move.player.label} move must have {expected_length} destination(s); "
                    f"got {len(move.destinations)}"
                )
            return move

        if state.current_player is PlayerRole.COP:
            if state.cop_count != 1:
                raise ValueError("integer cop moves are only valid when there is exactly one cop")
            return Move.cop((move,))
        return Move.robber(move)

    def _current_vertices_for_player(self, state: GameState, player: PlayerRole) -> tuple[int, ...]:
        if player is PlayerRole.COP:
            return state.cop_positions
        return (state.robber_position,)

    def _validate_cop_index(self, state: GameState, cop_index: int) -> None:
        if not 0 <= cop_index < state.cop_count:
            raise ValueError(f"cop index must satisfy 0 <= index < {state.cop_count}; got {cop_index}")
