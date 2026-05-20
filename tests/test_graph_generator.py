import pytest

from cops_and_robbers.core.graph_generator import generate_connected_graph


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


@pytest.mark.parametrize("n,m", [(10, 8), (10, 46), (2, 1), (31, 30)])
def test_invalid_graph_parameters_are_rejected(n: int, m: int) -> None:
    with pytest.raises(ValueError):
        generate_connected_graph(n=n, m=m, seed=123)
