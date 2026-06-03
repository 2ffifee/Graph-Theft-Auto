"""Validation helpers for graph and game settings."""

MIN_VERTICES = 3
MAX_VERTICES = 30
MIN_ROUNDS = 1
MAX_ROUNDS = 200
GRAPH_TYPE_ANY = "any"
GRAPH_TYPE_TREE = "tree"
GRAPH_TYPE_PLANAR = "planar"
GRAPH_TYPES = (GRAPH_TYPE_ANY, GRAPH_TYPE_TREE, GRAPH_TYPE_PLANAR)


def max_edges_for_vertices(n: int) -> int:
    return n * (n - 1) // 2


def max_planar_edges_for_vertices(n: int) -> int:
    validate_vertex_count(n)
    return 3 * n - 6


def edge_bounds_for_graph_type(n: int, graph_type: str = GRAPH_TYPE_ANY) -> tuple[int, int]:
    validate_vertex_count(n)
    if graph_type == GRAPH_TYPE_ANY:
        return n - 1, max_edges_for_vertices(n)
    if graph_type == GRAPH_TYPE_TREE:
        return n - 1, n - 1
    if graph_type == GRAPH_TYPE_PLANAR:
        return n - 1, max_planar_edges_for_vertices(n)
    raise ValueError(f"unknown graph type: {graph_type}")


def validate_vertex_count(n: int) -> None:
    if not MIN_VERTICES <= n <= MAX_VERTICES:
        raise ValueError(f"n must satisfy {MIN_VERTICES} <= n <= {MAX_VERTICES}; got {n}")


def validate_edge_count(n: int, m: int, graph_type: str = GRAPH_TYPE_ANY) -> None:
    min_edges, max_edges = edge_bounds_for_graph_type(n, graph_type)
    if not min_edges <= m <= max_edges:
        suffix = "" if graph_type == GRAPH_TYPE_ANY else f" ({graph_type})"
        raise ValueError(f"m must satisfy {min_edges} <= m <= {max_edges} for n={n}{suffix}; got {m}")


def validate_round_limit(round_limit: int) -> None:
    if not MIN_ROUNDS <= round_limit <= MAX_ROUNDS:
        raise ValueError(
            f"round limit must satisfy {MIN_ROUNDS} <= T <= {MAX_ROUNDS}; got {round_limit}"
        )


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))
