from cops_and_robbers.bots.greedy_bot import GreedyBot
from cops_and_robbers.bots.random_bot import RandomBot
from cops_and_robbers.core.game_rules import GameRules
from cops_and_robbers.core.game_state import GameState
from cops_and_robbers.core.graph_model import GraphModel
from cops_and_robbers.core.move import Move
from cops_and_robbers.core.player import PlayerRole


def path_graph_4() -> GraphModel:
    graph = GraphModel(4)
    graph.add_edge(0, 1)
    graph.add_edge(1, 2)
    graph.add_edge(2, 3)
    return graph


def test_random_bot_returns_legal_joint_cop_move() -> None:
    state = GameState(graph=path_graph_4(), cop_positions=(0, 1), robber_position=3, round_limit=10)
    rules = GameRules()
    legal_moves = rules.get_legal_cop_moves(state)
    bot = RandomBot(PlayerRole.COP, seed=1)

    move = bot.choose_move(state, legal_moves)

    assert move in legal_moves


def test_greedy_bot_returns_legal_joint_cop_move() -> None:
    state = GameState(graph=path_graph_4(), cop_positions=(0, 1), robber_position=3, round_limit=10)
    rules = GameRules()
    legal_moves = rules.get_legal_cop_moves(state)
    bot = GreedyBot(PlayerRole.COP, seed=1)

    move = bot.choose_move(state, legal_moves)

    assert isinstance(move, Move)
    assert move in legal_moves


def test_greedy_robber_maximizes_distance_from_nearest_cop() -> None:
    state = GameState(
        graph=path_graph_4(),
        cop_positions=(0, 1),
        robber_position=2,
        round_limit=10,
        current_player=PlayerRole.ROBBER,
    )
    rules = GameRules()
    legal_moves = rules.get_legal_robber_destinations(state)
    bot = GreedyBot(PlayerRole.ROBBER, seed=1)

    move = bot.choose_move(state, legal_moves)

    assert move == 3
