"""Graph generation routines."""

from __future__ import annotations

import random

import networkx as nx

from cops_and_robbers.core.graph_model import GraphModel
from cops_and_robbers.utils.validation import (
    GRAPH_TYPE_ANY,
    GRAPH_TYPE_PLANAR,
    GRAPH_TYPE_TREE,
    validate_edge_count,
)


def generate_connected_graph(
    n: int,
    m: int,
    seed: int | None = None,
    graph_type: str = GRAPH_TYPE_ANY,
) -> GraphModel:
    validate_edge_count(n, m, graph_type)
    rng = random.Random(seed)
    if graph_type == GRAPH_TYPE_TREE:
        return _generate_random_tree(n, rng)
    if graph_type == GRAPH_TYPE_PLANAR:
        return _generate_connected_planar_graph(n, m, rng)
    if graph_type != GRAPH_TYPE_ANY:
        raise ValueError(f"unknown graph type: {graph_type}")

    return _generate_connected_graph(n, m, rng)


def _generate_connected_graph(n: int, m: int, rng: random.Random) -> GraphModel:
    graph = GraphModel(n)

    # This generator guarantees connectedness and an exact edge count by first
    # generating a random spanning tree and then adding random extra edges.
    # It is efficient and suitable for gameplay, but it is not a uniform sampler
    # over all connected graphs with n vertices and m edges.
    for v in range(1, n):
        u = rng.randrange(0, v)
        graph.add_edge(u, v)

    possible_extra_edges: list[tuple[int, int]] = []
    for i in range(n):
        for j in range(i + 1, n):
            if not graph.has_edge(i, j):
                possible_extra_edges.append((i, j))

    rng.shuffle(possible_extra_edges)
    extra_index = 0
    while graph.edge_count < m:
        u, v = possible_extra_edges[extra_index]
        graph.add_edge(u, v)
        extra_index += 1

    return graph


def _generate_random_tree(n: int, rng: random.Random) -> GraphModel:
    graph = GraphModel(n)
    for v in range(1, n):
        graph.add_edge(rng.randrange(0, v), v)
    return graph


def _generate_connected_planar_graph(n: int, m: int, rng: random.Random) -> GraphModel:
    # Start with a tree to guarantee connectedness, then greedily add random
    # edges only when planarity is preserved.
    for _ in range(200):
        graph = _generate_random_tree(n, rng)
        possible_edges = [
            (i, j)
            for i in range(n)
            for j in range(i + 1, n)
            if not graph.has_edge(i, j)
        ]
        rng.shuffle(possible_edges)

        while graph.edge_count < m and possible_edges:
            u, v = possible_edges.pop()
            candidate = graph.to_networkx()
            candidate.add_edge(u, v)
            if nx.check_planarity(candidate)[0]:
                graph.add_edge(u, v)

        if graph.edge_count == m:
            return graph

    raise RuntimeError(f"failed to generate planar graph with n={n}, m={m}")
