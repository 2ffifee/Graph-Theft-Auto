import pytest

from cops_and_robbers.core.game_rules import GameRules
from cops_and_robbers.core.game_state import GameState, GameStatus
from cops_and_robbers.core.graph_model import GraphModel
from cops_and_robbers.core.move import Move
from cops_and_robbers.core.player import PlayerRole


def path_graph() -> GraphModel:
    graph = GraphModel(3)
    graph.add_edge(0, 1)
    graph.add_edge(1, 2)
    return graph


def path_graph_4() -> GraphModel:
    graph = GraphModel(4)
    graph.add_edge(0, 1)
    graph.add_edge(1, 2)
    graph.add_edge(2, 3)
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


def test_any_cop_can_capture_robber() -> None:
    state = GameState(
        graph=path_graph(),
        cop_positions=(0, 2),
        robber_position=2,
        round_limit=10,
    )
    rules = GameRules()

    assert rules.check_capture(state)


def test_multi_cop_legal_moves_are_cartesian_product() -> None:
    state = GameState(
        graph=path_graph_4(),
        cop_positions=(0, 2),
        robber_position=3,
        round_limit=10,
    )
    rules = GameRules()

    legal_moves = rules.get_legal_cop_moves(state)

    assert legal_moves == [
        Move.cop((0, 1)),
        Move.cop((0, 2)),
        Move.cop((0, 3)),
        Move.cop((1, 1)),
        Move.cop((1, 2)),
        Move.cop((1, 3)),
    ]


def test_structured_joint_cop_move_updates_all_cops() -> None:
    state = GameState(
        graph=path_graph_4(),
        cop_positions=(0, 2),
        robber_position=3,
        round_limit=10,
    )
    rules = GameRules()

    rules.apply_move(state, Move.cop((1, 2)))

    assert state.cop_positions == (1, 2)
    assert state.current_player is PlayerRole.ROBBER
    assert state.current_round == 1
    assert state.move_history[-1].from_vertices == (0, 2)
    assert state.move_history[-1].to_vertices == (1, 2)


def test_joint_cop_move_can_capture_with_any_cop() -> None:
    state = GameState(
        graph=path_graph_4(),
        cop_positions=(0, 2),
        robber_position=3,
        round_limit=10,
    )
    rules = GameRules()

    rules.apply_move(state, Move.cop((1, 3)))

    assert state.status is GameStatus.COP_WIN


def test_illegal_joint_cop_move_is_rejected() -> None:
    state = GameState(
        graph=path_graph_4(),
        cop_positions=(0, 2),
        robber_position=3,
        round_limit=10,
    )
    rules = GameRules()

    with pytest.raises(ValueError):
        rules.apply_move(state, Move.cop((2, 2)))


def test_joint_cop_move_requires_one_destination_per_cop() -> None:
    state = GameState(
        graph=path_graph_4(),
        cop_positions=(0, 2),
        robber_position=3,
        round_limit=10,
    )
    rules = GameRules()

    with pytest.raises(ValueError):
        rules.apply_move(state, Move.cop((1,)))


def test_integer_cop_move_is_rejected_when_multiple_cops_exist() -> None:
    state = GameState(
        graph=path_graph_4(),
        cop_positions=(0, 2),
        robber_position=3,
        round_limit=10,
    )
    rules = GameRules()

    with pytest.raises(ValueError):
        rules.apply_move(state, 1)
