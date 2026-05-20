"""Graph generation routines."""

from __future__ import annotations

import random

from cops_and_robbers.core.graph_model import GraphModel
from cops_and_robbers.utils.validation import validate_edge_count


def generate_connected_graph(n: int, m: int, seed: int | None = None) -> GraphModel:
    validate_edge_count(n, m)
    rng = random.Random(seed)
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
