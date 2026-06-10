import random

from cops_and_robbers.core.graph_model import GraphModel
from cops_and_robbers.experiments.runner import place_heuristic


def path_graph(n: int) -> GraphModel:
    graph = GraphModel(n)
    for vertex in range(n - 1):
        graph.add_edge(vertex, vertex + 1)
    return graph


def test_heuristic_placement_chooses_center_for_one_cop() -> None:
    graph = path_graph(5)

    cops, robber = place_heuristic(graph, n_cops=1, rng=random.Random(1))

    assert cops == (2,)
    assert robber in {0, 4}


def test_heuristic_placement_prefers_central_vertices_for_multiple_cops() -> None:
    graph = path_graph(5)

    cops, robber = place_heuristic(graph, n_cops=2, rng=random.Random(1))

    assert 2 in cops
    assert set(cops) <= {1, 2, 3}
    assert robber in {0, 4}
