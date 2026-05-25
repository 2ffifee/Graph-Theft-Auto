from cops_and_robbers.core.graph_model import GraphModel
from cops_and_robbers.ui.graph_layout import GraphLayout, count_edge_crossings


def cycle_graph(n: int) -> GraphModel:
    graph = GraphModel(n)
    for vertex in range(n):
        graph.add_edge(vertex, (vertex + 1) % n)
    return graph


def complete_bipartite_3_3() -> GraphModel:
    graph = GraphModel(6)
    for left in range(3):
        for right in range(3, 6):
            graph.add_edge(left, right)
    return graph


def test_planar_graph_uses_planar_layout() -> None:
    layout = GraphLayout(cycle_graph(6), width=600, height=400)

    assert layout.layout_method == "planar"
    assert layout.edge_crossings == 0


def test_nonplanar_graph_uses_crossing_minimized_layout() -> None:
    layout = GraphLayout(complete_bipartite_3_3(), width=600, height=400, spring_attempts=3)

    assert layout.layout_method == "crossing-minimized"


def test_crossing_counter_ignores_edges_with_shared_endpoint() -> None:
    edges = [(0, 1), (1, 2)]
    positions = {0: (0.0, 0.0), 1: (1.0, 1.0), 2: (2.0, 0.0)}

    assert count_edge_crossings(edges, positions) == 0


def test_crossing_counter_detects_proper_crossing() -> None:
    edges = [(0, 1), (2, 3)]
    positions = {
        0: (0.0, 0.0),
        1: (2.0, 2.0),
        2: (0.0, 2.0),
        3: (2.0, 0.0),
    }

    assert count_edge_crossings(edges, positions) == 1
