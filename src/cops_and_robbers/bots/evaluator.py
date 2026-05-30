"""Heuristic evaluation for search-based bots."""

from __future__ import annotations

from collections import deque

from cops_and_robbers.core.game_state import GameState, GameStatus


class HeuristicEvaluator:
    CAPTURE_SCORE = 1_000_000
    NEAREST_COP_DISTANCE_WEIGHT = 35
    TOTAL_COP_DISTANCE_WEIGHT = 6
    ROBBER_MOBILITY_WEIGHT = 12
    SAFE_ROBBER_MOBILITY_WEIGHT = 10
    COP_MOBILITY_WEIGHT = 2
    ESCAPE_SPACE_WEIGHT = 4
    SAFE_ESCAPE_SPACE_WEIGHT = 6
    LEAF_TRAP_BONUS = 18
    DEGREE_TWO_TRAP_BONUS = 8

    def evaluate(self, state: GameState) -> float:
        """Return a score where larger values are better for the cops."""
        if state.status is GameStatus.COP_WIN or state.robber_position in state.cop_positions:
            return self.CAPTURE_SCORE
        if state.status is GameStatus.ROBBER_WIN:
            return -self.CAPTURE_SCORE

        cop_distances = [
            state.graph.shortest_distance(cop_position, state.robber_position)
            for cop_position in state.cop_positions
        ]
        nearest_cop_distance = min(cop_distances)
        total_cop_distance = sum(cop_distances)
        robber_mobility = len(state.graph.legal_moves(state.robber_position))
        controlled_vertices = self._cop_controlled_vertices(state)
        safe_robber_mobility = sum(
            1
            for destination in state.graph.legal_moves(state.robber_position)
            if destination not in controlled_vertices
        )
        cop_mobility = sum(len(state.graph.legal_moves(cop_position)) for cop_position in state.cop_positions)
        escape_vertices = self._vertices_within_radius(state, state.robber_position, radius=2)
        escape_space = len(escape_vertices)
        safe_escape_space = sum(
            1
            for vertex in escape_vertices
            if vertex not in controlled_vertices
        )
        trap_bonus = self._trap_bonus(state)

        return (
            -self.NEAREST_COP_DISTANCE_WEIGHT * nearest_cop_distance
            - self.TOTAL_COP_DISTANCE_WEIGHT * total_cop_distance
            - self.ROBBER_MOBILITY_WEIGHT * robber_mobility
            - self.SAFE_ROBBER_MOBILITY_WEIGHT * safe_robber_mobility
            + self.COP_MOBILITY_WEIGHT * cop_mobility
            - self.ESCAPE_SPACE_WEIGHT * escape_space
            - self.SAFE_ESCAPE_SPACE_WEIGHT * safe_escape_space
            + trap_bonus
        )

    def _trap_bonus(self, state: GameState) -> int:
        robber_degree = len(state.graph.neighbors(state.robber_position))
        if robber_degree <= 1:
            return self.LEAF_TRAP_BONUS
        if robber_degree == 2:
            return self.DEGREE_TWO_TRAP_BONUS
        return 0

    def _vertices_within_radius(self, state: GameState, start: int, radius: int) -> set[int]:
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

        return seen

    def _cop_controlled_vertices(self, state: GameState) -> set[int]:
        controlled: set[int] = set()
        for cop_position in state.cop_positions:
            controlled.update(state.graph.closed_neighbors(cop_position))
        return controlled
