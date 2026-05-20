import pytest

from cops_and_robbers.core.game_rules import GameRules
from cops_and_robbers.core.game_state import GameState, GameStatus
from cops_and_robbers.core.graph_model import GraphModel
from cops_and_robbers.core.player import PlayerRole


def path_graph() -> GraphModel:
    graph = GraphModel(3)
    graph.add_edge(0, 1)
    graph.add_edge(1, 2)
    return graph


def test_legal_moves_include_staying_still_and_neighbors() -> None:
    state = GameState(graph=path_graph(), cop_position=1, robber_position=2, round_limit=10)
    rules = GameRules()

    assert rules.get_legal_moves(state) == [0, 1, 2]


def test_illegal_non_neighbor_move_is_rejected() -> None:
    state = GameState(graph=path_graph(), cop_position=0, robber_position=2, round_limit=10)
    rules = GameRules()

    assert not rules.is_legal_move(state, 2)
    with pytest.raises(ValueError):
        rules.apply_move(state, 2)


def test_cop_wins_when_positions_coincide_after_cop_move() -> None:
    state = GameState(graph=path_graph(), cop_position=0, robber_position=1, round_limit=10)
    rules = GameRules()

    rules.apply_move(state, 1)

    assert state.status is GameStatus.COP_WIN


def test_robber_moving_onto_cop_counts_as_capture() -> None:
    state = GameState(
        graph=path_graph(),
        cop_position=1,
        robber_position=2,
        round_limit=10,
        current_player=PlayerRole.ROBBER,
    )
    rules = GameRules()

    rules.apply_move(state, 1)

    assert state.status is GameStatus.COP_WIN


def test_robber_wins_after_surviving_final_round() -> None:
    state = GameState(
        graph=path_graph(),
        cop_position=0,
        robber_position=2,
        round_limit=1,
        current_player=PlayerRole.ROBBER,
        current_round=1,
    )
    rules = GameRules()

    rules.apply_move(state, 2)

    assert state.status is GameStatus.ROBBER_WIN
    assert state.current_round == 1


def test_capture_precedes_final_round_survival() -> None:
    state = GameState(
        graph=path_graph(),
        cop_position=1,
        robber_position=2,
        round_limit=1,
        current_player=PlayerRole.ROBBER,
        current_round=1,
    )
    rules = GameRules()

    rules.apply_move(state, 1)

    assert state.status is GameStatus.COP_WIN
