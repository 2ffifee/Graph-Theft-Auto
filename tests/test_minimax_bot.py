from cops_and_robbers.bots.evaluator import HeuristicEvaluator
from cops_and_robbers.bots.minimax_bot import MinimaxBot
from cops_and_robbers.core.game_rules import GameRules
from cops_and_robbers.core.game_state import GameState
from cops_and_robbers.core.graph_model import GraphModel
from cops_and_robbers.core.player import PlayerRole


def path_graph(n: int) -> GraphModel:
    graph = GraphModel(n)
    for vertex in range(n - 1):
        graph.add_edge(vertex, vertex + 1)
    return graph


def test_minimax_cop_takes_immediate_capture() -> None:
    state = GameState(graph=path_graph(3), cop_position=0, robber_position=1, round_limit=10)
    rules = GameRules()
    bot = MinimaxBot(role=PlayerRole.COP, depth=2, seed=1)

    move = bot.choose_move(state, rules.get_legal_moves(state))

    assert move == 1


def test_minimax_robber_avoids_immediate_capture() -> None:
    state = GameState(
        graph=path_graph(3),
        cop_position=1,
        robber_position=2,
        round_limit=10,
        current_player=PlayerRole.ROBBER,
    )
    rules = GameRules()
    bot = MinimaxBot(role=PlayerRole.ROBBER, depth=1, seed=1)

    move = bot.choose_move(state, rules.get_legal_moves(state))

    assert move == 2


def test_minimax_move_is_always_legal() -> None:
    state = GameState(graph=path_graph(5), cop_position=0, robber_position=4, round_limit=10)
    rules = GameRules()
    legal_moves = rules.get_legal_moves(state)
    bot = MinimaxBot(role=PlayerRole.COP, depth=3, seed=1)

    move = bot.choose_move(state, legal_moves)

    assert move in legal_moves


def test_evaluator_prefers_smaller_cop_robber_distance() -> None:
    graph = path_graph(5)
    evaluator = HeuristicEvaluator()
    far_state = GameState(graph=graph, cop_position=0, robber_position=4, round_limit=10)
    near_state = GameState(graph=graph, cop_position=3, robber_position=4, round_limit=10)

    assert evaluator.evaluate(near_state) > evaluator.evaluate(far_state)


def test_minimax_does_not_mutate_real_state_while_searching() -> None:
    state = GameState(graph=path_graph(4), cop_position=0, robber_position=3, round_limit=10)
    rules = GameRules()
    bot = MinimaxBot(role=PlayerRole.COP, depth=3, seed=1)

    bot.choose_move(state, rules.get_legal_moves(state))

    assert state.cop_position == 0
    assert state.robber_position == 3
    assert state.current_player is PlayerRole.COP
    assert state.current_round == 1
    assert state.move_history == []
