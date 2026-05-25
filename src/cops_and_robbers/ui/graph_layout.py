"""Graph layout calculation and vertex hit testing."""

from __future__ import annotations

from itertools import combinations

import networkx as nx

from cops_and_robbers.core.graph_model import GraphModel

Point = tuple[float, float]


class GraphLayout:
    def __init__(
        self,
        graph: GraphModel,
        width: int,
        height: int,
        margin: int = 60,
        origin: tuple[int, int] = (0, 0),
        seed: int = 7,
        spring_attempts: int = 24,
    ):
        self.graph = graph
        self.width = width
        self.height = height
        self.margin = margin
        self.origin = origin
        self.seed = seed
        self.spring_attempts = spring_attempts
        self.layout_method = "spring"
        self.edge_crossings = 0
        self.positions = self.compute_positions()

    def compute_positions(self) -> dict[int, tuple[float, float]]:
        nx_graph = self.graph.to_networkx()
        raw_positions = self._choose_raw_positions(nx_graph)
        self.edge_crossings = count_edge_crossings(self.graph.edges(), raw_positions)
        if self.layout_method == "planar":
            self.edge_crossings = 0
        return self._fit_positions(raw_positions)

    def get_vertex_at_position(self, x: int, y: int, radius: int) -> int | None:
        radius_squared = radius * radius
        for vertex, (vx, vy) in self.positions.items():
            dx = x - vx
            dy = y - vy
            if dx * dx + dy * dy <= radius_squared:
                return vertex
        return None

    def _choose_raw_positions(self, nx_graph: nx.Graph) -> dict[int, Point]:
        is_planar, _embedding = nx.check_planarity(nx_graph)
        if is_planar:
            self.layout_method = "planar"
            return _as_plain_positions(nx.planar_layout(nx_graph))

        self.layout_method = "crossing-minimized"
        best_positions = _as_plain_positions(nx.spring_layout(nx_graph, seed=self.seed))
        best_crossings = count_edge_crossings(self.graph.edges(), best_positions)

        for offset in range(1, self.spring_attempts):
            candidate = _as_plain_positions(nx.spring_layout(nx_graph, seed=self.seed + offset))
            crossings = count_edge_crossings(self.graph.edges(), candidate)
            if crossings < best_crossings:
                best_positions = candidate
                best_crossings = crossings
                if best_crossings == 0:
                    break

        return best_positions

    def _fit_positions(self, raw_positions: dict[int, Point]) -> dict[int, Point]:
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


def count_edge_crossings(edges: list[tuple[int, int]], positions: dict[int, Point]) -> int:
    crossings = 0
    for (a, b), (c, d) in combinations(edges, 2):
        if len({a, b, c, d}) < 4:
            continue
        if _segments_intersect(positions[a], positions[b], positions[c], positions[d]):
            crossings += 1
    return crossings


def _segments_intersect(p1: Point, p2: Point, q1: Point, q2: Point) -> bool:
    o1 = _orientation(p1, p2, q1)
    o2 = _orientation(p1, p2, q2)
    o3 = _orientation(q1, q2, p1)
    o4 = _orientation(q1, q2, p2)

    if o1 == 0 and _on_segment(p1, q1, p2):
        return True
    if o2 == 0 and _on_segment(p1, q2, p2):
        return True
    if o3 == 0 and _on_segment(q1, p1, q2):
        return True
    if o4 == 0 and _on_segment(q1, p2, q2):
        return True

    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def _orientation(a: Point, b: Point, c: Point) -> int:
    value = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])
    epsilon = 1e-9
    if abs(value) < epsilon:
        return 0
    return 1 if value > 0 else -1


def _on_segment(a: Point, b: Point, c: Point) -> bool:
    return (
        min(a[0], c[0]) <= b[0] <= max(a[0], c[0])
        and min(a[1], c[1]) <= b[1] <= max(a[1], c[1])
    )


def _as_plain_positions(raw_positions: dict[int, object]) -> dict[int, Point]:
    return {int(vertex): (float(position[0]), float(position[1])) for vertex, position in raw_positions.items()}
