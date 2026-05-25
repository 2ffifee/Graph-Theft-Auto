"""Heuristic evaluation for depth-limited search bots."""

from __future__ import annotations

from collections import deque

from cops_and_robbers.core.game_state import GameState, GameStatus


class HeuristicEvaluator:
    CAPTURE_SCORE = 1_000_000
    DISTANCE_WEIGHT = 20
    ROBBER_MOBILITY_WEIGHT = 8
    COP_MOBILITY_WEIGHT = 3
    ESCAPE_SPACE_WEIGHT = 2
    LEAF_TRAP_BONUS = 15
    DEGREE_TWO_TRAP_BONUS = 7

    def evaluate(self, state: GameState) -> float:
        """Return a score where positive is good for the cop."""
        if state.status is GameStatus.COP_WIN or state.cop_position == state.robber_position:
            return self.CAPTURE_SCORE
        if state.status is GameStatus.ROBBER_WIN:
            return -self.CAPTURE_SCORE

        distance = state.graph.shortest_distance(state.cop_position, state.robber_position)
        robber_moves = len(state.graph.legal_moves(state.robber_position))
        cop_moves = len(state.graph.legal_moves(state.cop_position))
        escape_space = self._vertices_within_radius(state, state.robber_position, radius=2)
        trap_bonus = self._trap_bonus(state)

        return (
            -self.DISTANCE_WEIGHT * distance
            - self.ROBBER_MOBILITY_WEIGHT * robber_moves
            + self.COP_MOBILITY_WEIGHT * cop_moves
            - self.ESCAPE_SPACE_WEIGHT * escape_space
            + trap_bonus
        )

    def _trap_bonus(self, state: GameState) -> int:
        robber_degree = len(state.graph.neighbors(state.robber_position))
        if robber_degree <= 1:
            return self.LEAF_TRAP_BONUS
        if robber_degree == 2:
            return self.DEGREE_TWO_TRAP_BONUS
        return 0

    def _vertices_within_radius(self, state: GameState, start: int, radius: int) -> int:
        seen = {start}
        queue: deque[tuple[int, int]] = deque([(start, 0)])

        while queue:
            vertex, distance = queue.popleft()
            if distance >= radius:
                continue
            for neighbor in state.graph.neighbors(vertex):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append((neighbor, distance + 1))

        return len(seen)
