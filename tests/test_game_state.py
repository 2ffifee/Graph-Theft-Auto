from cops_and_robbers.core.game_rules import GameRules
from cops_and_robbers.core.game_state import GameState
from cops_and_robbers.core.graph_model import GraphModel
from cops_and_robbers.core.player import PlayerRole


def path_graph() -> GraphModel:
    graph = GraphModel(3)
    graph.add_edge(0, 1)
    graph.add_edge(1, 2)
    return graph


def test_current_player_switches_after_cop_move() -> None:
    state = GameState(graph=path_graph(), cop_position=0, robber_position=2, round_limit=10)
    rules = GameRules()

    rules.apply_move(state, 1)

    assert state.current_player is PlayerRole.ROBBER


def test_round_increments_after_robber_move() -> None:
    state = GameState(
        graph=path_graph(),
        cop_position=0,
        robber_position=2,
        round_limit=10,
        current_player=PlayerRole.ROBBER,
    )
    rules = GameRules()

    rules.apply_move(state, 2)

    assert state.current_round == 2
    assert state.current_player is PlayerRole.COP


def test_round_does_not_increment_after_cop_move() -> None:
    state = GameState(graph=path_graph(), cop_position=0, robber_position=2, round_limit=10)
    rules = GameRules()

    rules.apply_move(state, 1)

    assert state.current_round == 1
