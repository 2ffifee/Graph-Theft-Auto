"""Validation helpers for graph and game settings."""

MIN_VERTICES = 3
MAX_VERTICES = 30
MIN_ROUNDS = 1
MAX_ROUNDS = 200


def max_edges_for_vertices(n: int) -> int:
    return n * (n - 1) // 2


def validate_vertex_count(n: int) -> None:
    if not MIN_VERTICES <= n <= MAX_VERTICES:
        raise ValueError(f"n must satisfy {MIN_VERTICES} <= n <= {MAX_VERTICES}; got {n}")


def validate_edge_count(n: int, m: int) -> None:
    validate_vertex_count(n)
    min_edges = n - 1
    max_edges = max_edges_for_vertices(n)
    if not min_edges <= m <= max_edges:
        raise ValueError(f"m must satisfy {min_edges} <= m <= {max_edges} for n={n}; got {m}")


def validate_round_limit(round_limit: int) -> None:
    if not MIN_ROUNDS <= round_limit <= MAX_ROUNDS:
        raise ValueError(
            f"round limit must satisfy {MIN_ROUNDS} <= T <= {MAX_ROUNDS}; got {round_limit}"
        )


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))
