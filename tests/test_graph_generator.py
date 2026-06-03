import pytest
import networkx as nx

from cops_and_robbers.core.graph_generator import generate_connected_graph
from cops_and_robbers.utils.validation import (
    GRAPH_TYPE_PLANAR,
    GRAPH_TYPE_TREE,
)


def test_connected_graph_has_requested_size() -> None:
    graph = generate_connected_graph(n=10, m=15, seed=123)

    assert graph.n == 10
    assert graph.edge_count == 15
    assert graph.is_connected()


def test_tree_edge_count_is_allowed() -> None:
    graph = generate_connected_graph(n=6, m=5, seed=123)

    assert graph.n == 6
    assert graph.edge_count == 5
    assert graph.is_connected()


def test_complete_edge_count_is_allowed() -> None:
    graph = generate_connected_graph(n=5, m=10, seed=123)

    assert graph.n == 5
    assert graph.edge_count == 10
    assert graph.is_connected()


def test_tree_graph_type_generates_tree() -> None:
    graph = generate_connected_graph(n=8, m=7, seed=123, graph_type=GRAPH_TYPE_TREE)

    assert graph.n == 8
    assert graph.edge_count == 7
    assert graph.is_connected()
    assert nx.is_tree(graph.to_networkx())


def test_planar_graph_type_generates_planar_graph() -> None:
    graph = generate_connected_graph(n=10, m=20, seed=123, graph_type=GRAPH_TYPE_PLANAR)

    assert graph.n == 10
    assert graph.edge_count == 20
    assert graph.is_connected()
    assert nx.check_planarity(graph.to_networkx())[0]


@pytest.mark.parametrize("n,m", [(10, 8), (10, 46), (2, 1), (31, 30)])
def test_invalid_graph_parameters_are_rejected(n: int, m: int) -> None:
    with pytest.raises(ValueError):
        generate_connected_graph(n=n, m=m, seed=123)


@pytest.mark.parametrize(
    "n,m,graph_type",
    [
        (6, 6, GRAPH_TYPE_TREE),
        (6, 13, GRAPH_TYPE_PLANAR),
    ],
)
def test_invalid_graph_type_edge_counts_are_rejected(n: int, m: int, graph_type: str) -> None:
    with pytest.raises(ValueError):
        generate_connected_graph(n=n, m=m, seed=123, graph_type=graph_type)
