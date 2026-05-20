"""Graph layout calculation and vertex hit testing."""

from __future__ import annotations

import networkx as nx

from cops_and_robbers.core.graph_model import GraphModel


class GraphLayout:
    def __init__(
        self,
        graph: GraphModel,
        width: int,
        height: int,
        margin: int = 60,
        origin: tuple[int, int] = (0, 0),
        seed: int = 7,
    ):
        self.graph = graph
        self.width = width
        self.height = height
        self.margin = margin
        self.origin = origin
        self.seed = seed
        self.positions = self.compute_positions()

    def compute_positions(self) -> dict[int, tuple[float, float]]:
        raw_positions = nx.spring_layout(self.graph.to_networkx(), seed=self.seed)
        xs = [float(pos[0]) for pos in raw_positions.values()]
        ys = [float(pos[1]) for pos in raw_positions.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        span_x = max(max_x - min_x, 1e-9)
        span_y = max(max_y - min_y, 1e-9)

        usable_width = max(1, self.width - 2 * self.margin)
        usable_height = max(1, self.height - 2 * self.margin)
        origin_x, origin_y = self.origin

        positions: dict[int, tuple[float, float]] = {}
        for vertex, pos in raw_positions.items():
            norm_x = (float(pos[0]) - min_x) / span_x
            norm_y = (float(pos[1]) - min_y) / span_y
            x = origin_x + self.margin + norm_x * usable_width
            y = origin_y + self.margin + norm_y * usable_height
            positions[int(vertex)] = (x, y)
        return positions

    def get_vertex_at_position(self, x: int, y: int, radius: int) -> int | None:
        radius_squared = radius * radius
        for vertex, (vx, vy) in self.positions.items():
            dx = x - vx
            dy = y - vy
            if dx * dx + dy * dy <= radius_squared:
                return vertex
        return None
