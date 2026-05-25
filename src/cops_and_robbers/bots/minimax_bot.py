"""Depth-limited minimax bot with alpha-beta pruning."""

from __future__ import annotations

import math
import random

from cops_and_robbers.bots.bot_base import BotBase
from cops_and_robbers.bots.evaluator import HeuristicEvaluator
from cops_and_robbers.core.game_rules import GameRules
from cops_and_robbers.core.game_state import GameState, GameStatus
from cops_and_robbers.core.player import PlayerRole


class MinimaxBot(BotBase):
    def __init__(
        self,
        role: PlayerRole,
        depth: int,
        evaluator: HeuristicEvaluator | None = None,
        seed: int | None = None,
    ):
        super().__init__(role)
        if depth < 1:
            raise ValueError("minimax depth must be at least 1")
        self.depth = depth
        self.evaluator = evaluator or HeuristicEvaluator()
        self.rules = GameRules()
        self._rng = random.Random(seed)

    def choose_move(self, state: GameState, legal_moves: list[int]) -> int:
        if not legal_moves:
            raise ValueError("legal_moves must not be empty")

        scored_moves: list[tuple[float, int]] = []
        for move in sorted(legal_moves):
            child = state.clone()
            self.rules.apply_move(child, move)
            score = self._search(
                child,
                depth_remaining=self.depth - 1,
                alpha=-math.inf,
                beta=math.inf,
                ply_from_root=1,
                cache={},
            )
            scored_moves.append((score, move))

        if self.role is PlayerRole.COP:
            best_score = max(score for score, _move in scored_moves)
        else:
            best_score = min(score for score, _move in scored_moves)

        best_moves = [move for score, move in scored_moves if score == best_score]
        return self._rng.choice(best_moves)

    def _search(
        self,
        state: GameState,
        depth_remaining: int,
        alpha: float,
        beta: float,
        ply_from_root: int,
        cache: dict[tuple[int, int, PlayerRole, int, GameStatus, int], float],
    ) -> float:
        terminal_score = self._terminal_score(state, ply_from_root)
        if terminal_score is not None:
            return terminal_score
        if depth_remaining == 0:
            return self.evaluator.evaluate(state)

        key = (
            state.cop_position,
            state.robber_position,
            state.current_player,
            state.current_round,
            state.status,
            depth_remaining,
        )
        if key in cache:
            return cache[key]

        legal_moves = self.rules.get_legal_moves(state)
        if state.current_player is PlayerRole.COP:
            value = -math.inf
            for move in legal_moves:
                child = state.clone()
                self.rules.apply_move(child, move)
                value = max(
                    value,
                    self._search(child, depth_remaining - 1, alpha, beta, ply_from_root + 1, cache),
                )
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
        else:
            value = math.inf
            for move in legal_moves:
                child = state.clone()
                self.rules.apply_move(child, move)
                value = min(
                    value,
                    self._search(child, depth_remaining - 1, alpha, beta, ply_from_root + 1, cache),
                )
                beta = min(beta, value)
                if alpha >= beta:
                    break

        cache[key] = value
        return value

    def _terminal_score(self, state: GameState, ply_from_root: int) -> float | None:
        if state.status is GameStatus.COP_WIN or state.cop_position == state.robber_position:
            return self.evaluator.CAPTURE_SCORE - ply_from_root
        if state.status is GameStatus.ROBBER_WIN:
            return -self.evaluator.CAPTURE_SCORE + ply_from_root
        return None
