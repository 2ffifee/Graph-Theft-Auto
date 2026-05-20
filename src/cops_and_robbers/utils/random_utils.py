"""Random setup helpers."""

from __future__ import annotations

import random

from cops_and_robbers.core.graph_model import GraphModel


def choose_random_start_positions(graph: GraphModel, rng: random.Random) -> tuple[int, int]:
    vertices = graph.vertices()
    cop = rng.choice(vertices)
    robber = rng.choice([vertex for vertex in vertices if vertex != cop])
    return cop, robber
