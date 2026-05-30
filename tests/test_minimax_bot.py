from cops_and_robbers.bots.evaluator import HeuristicEvaluator
from cops_and_robbers.bots.minimax_bot import MinimaxBot
from cops_and_robbers.core.game_rules import GameRules
from cops_and_robbers.core.game_state import GameState
from cops_and_robbers.core.graph_model import GraphModel
from cops_and_robbers.core.move import Move
from cops_and_robbers.core.player import PlayerRole


def path_graph(n: int) -> GraphModel:
    graph = GraphModel(n)
    for vertex in range(n - 1):
        graph.add_edge(vertex, vertex + 1)
    return graph


def test_minimax_one_cop_takes_immediate_capture() -> None:
    state = GameState(graph=path_graph(3), cop_position=0, robber_position=1, round_limit=10)
    rules = GameRules()
    bot = MinimaxBot(role=PlayerRole.COP, depth=2, seed=1)

    move = bot.choose_move(state, rules.get_legal_moves(state))

    assert move == 1


def test_minimax_multi_cop_takes_immediate_capture() -> None:
    state = GameState(graph=path_graph(4), cop_positions=(0, 2), robber_position=3, round_limit=10)
    rules = GameRules()
    bot = MinimaxBot(role=PlayerRole.COP, depth=2, seed=1)

    move = bot.choose_move(state, rules.get_legal_cop_moves(state))

    assert isinstance(move, Move)
    assert 3 in move.destinations


def test_minimax_robber_avoids_immediate_capture_when_possible() -> None:
    state = GameState(
        graph=path_graph(4),
        cop_positions=(0, 1),
        robber_position=2,
        round_limit=10,
        current_player=PlayerRole.ROBBER,
    )
    rules = GameRules()
    bot = MinimaxBot(role=PlayerRole.ROBBER, depth=1, seed=1)

    move = bot.choose_move(state, rules.get_legal_robber_destinations(state))

    assert move == 3


def test_minimax_search_does_not_mutate_real_state() -> None:
    state = GameState(graph=path_graph(4), cop_positions=(0, 1), robber_position=3, round_limit=10)
    rules = GameRules()
    bot = MinimaxBot(role=PlayerRole.COP, depth=3, seed=1)

    bot.choose_move(state, rules.get_legal_cop_moves(state))

    assert state.cop_positions == (0, 1)
    assert state.robber_position == 3
    assert state.current_player is PlayerRole.COP
    assert state.move_history == []


def test_evaluator_prefers_nearer_cops() -> None:
    graph = path_graph(5)
    evaluator = HeuristicEvaluator()
    far_state = GameState(graph=graph, cop_positions=(0, 1), robber_position=4, round_limit=10)
    near_state = GameState(graph=graph, cop_positions=(2, 3), robber_position=4, round_limit=10)

    assert evaluator.evaluate(near_state) > evaluator.evaluate(far_state)


def test_evaluator_rewards_robber_escape_space() -> None:
    graph = GraphModel(7)
    graph.add_edge(0, 1)
    graph.add_edge(1, 2)
    graph.add_edge(2, 3)
    graph.add_edge(3, 4)
    graph.add_edge(4, 5)
    graph.add_edge(4, 6)
    evaluator = HeuristicEvaluator()
    cramped_state = GameState(graph=graph, cop_positions=(0,), robber_position=2, round_limit=10)
    open_state = GameState(graph=graph, cop_positions=(0,), robber_position=4, round_limit=10)

    assert evaluator.evaluate(open_state) < evaluator.evaluate(cramped_state)


def test_evaluator_rewards_safe_robber_mobility() -> None:
    graph = path_graph(5)
    evaluator = HeuristicEvaluator()
    unsafe_state = GameState(graph=graph, cop_positions=(1,), robber_position=2, round_limit=10)
    safer_state = GameState(graph=graph, cop_positions=(0,), robber_position=2, round_limit=10)

    assert evaluator.evaluate(safer_state) < evaluator.evaluate(unsafe_state)
