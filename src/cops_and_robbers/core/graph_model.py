"""Thin wrapper around a simple undirected NetworkX graph."""

from __future__ import annotations

import networkx as nx


class GraphModel:
    def __init__(self, n: int):
        if n <= 0:
            raise ValueError(f"n must be positive; got {n}")
        self._graph = nx.Graph()
        self._graph.add_nodes_from(range(n))
        self._distance_cache: dict[int, dict[int, int]] = {}

    @property
    def n(self) -> int:
        return self._graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self._graph.number_of_edges()

    def add_edge(self, u: int, v: int) -> None:
        self._validate_vertex(u)
        self._validate_vertex(v)
        if u == v:
            raise ValueError("self-loops are not allowed")
        self._graph.add_edge(u, v)
        self._distance_cache.clear()

    def has_edge(self, u: int, v: int) -> bool:
        self._validate_vertex(u)
        self._validate_vertex(v)
        return self._graph.has_edge(u, v)

    def vertices(self) -> list[int]:
        return sorted(self._graph.nodes)

    def edges(self) -> list[tuple[int, int]]:
        return sorted((min(u, v), max(u, v)) for u, v in self._graph.edges)

    def neighbors(self, vertex: int) -> list[int]:
        self._validate_vertex(vertex)
        return sorted(self._graph.neighbors(vertex))

    def closed_neighbors(self, vertex: int) -> list[int]:
        self._validate_vertex(vertex)
        return sorted([vertex, *self._graph.neighbors(vertex)])

    def legal_moves(self, vertex: int) -> list[int]:
        return self.closed_neighbors(vertex)

    def shortest_distance(self, source: int, target: int) -> int:
        self._validate_vertex(source)
        self._validate_vertex(target)
        if source not in self._distance_cache:
            self._distance_cache[source] = dict(nx.single_source_shortest_path_length(self._graph, source))
        return self._distance_cache[source][target]

    def is_connected(self) -> bool:
        return nx.is_connected(self._graph)

    def to_networkx(self) -> nx.Graph:
        """Return a defensive copy for algorithms that require NetworkX."""
        return self._graph.copy()

    def _validate_vertex(self, vertex: int) -> None:
        if vertex not in self._graph:
            raise ValueError(f"unknown vertex {vertex}")
