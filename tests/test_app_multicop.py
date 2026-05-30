import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from cops_and_robbers.core.player import PlayerRole
from cops_and_robbers.ui.app import AppScreen, BotLevel, CopsAndRobbersApp, GameMode


def click_vertex(app: CopsAndRobbersApp, vertex: int) -> None:
    assert app.layout is not None
    x, y = app.layout.positions[vertex]
    app._handle_placement_click((round(x), round(y)))


def click_game_vertex(app: CopsAndRobbersApp, vertex: int) -> None:
    assert app.layout is not None
    x, y = app.layout.positions[vertex]
    app._handle_game_click((round(x), round(y)))


def test_multicop_placement_selects_cops_then_robber() -> None:
    app = CopsAndRobbersApp(seed=123)
    app.setup_cop_count = 3
    app.start_new_game(6, 7, 10)

    assert app.current_screen is AppScreen.PLACEMENT

    click_vertex(app, 0)
    click_vertex(app, 1)
    click_vertex(app, 2)
    click_vertex(app, 2)

    assert app.state is None
    assert app.selected_cop_positions == [0, 1, 2]

    click_vertex(app, 3)

    assert app.current_screen is AppScreen.GAME
    assert app.state is not None
    assert app.state.cop_positions == (0, 1, 2)
    assert app.state.robber_position == 3


def test_multicop_game_render_does_not_raise() -> None:
    app = CopsAndRobbersApp(seed=123)
    app.setup_cop_count = 2
    app.start_new_game(6, 7, 10)
    app._start_on_selected_positions((0, 1), 3)

    app.render()


def test_staged_multicop_turn_applies_joint_move_after_all_cops_selected() -> None:
    app = CopsAndRobbersApp(seed=123)
    app.setup_cop_count = 2
    app.start_new_game(6, 7, 10)
    app._start_on_selected_positions((0, 1), 3)

    click_game_vertex(app, 0)

    assert app.state is not None
    assert app.staged_cop_destinations == [0]
    assert app.state.cop_positions == (0, 1)

    click_game_vertex(app, 1)

    assert app.staged_cop_destinations == []
    assert app.state.cop_positions == (0, 1)
    assert app.state.current_player.name == "ROBBER"
    assert app.state.move_history[-1].to_vertices == (0, 1)


def test_staged_multicop_turn_ignores_illegal_destination() -> None:
    app = CopsAndRobbersApp(seed=123)
    app.setup_cop_count = 2
    app.start_new_game(6, 5, 10)
    app._start_on_selected_positions((0, 1), 3)
    assert app.state is not None

    legal = set(app.rules.get_legal_cop_destinations(app.state, 0))
    illegal_vertices = [vertex for vertex in app.graph.vertices() if vertex not in legal]
    if not illegal_vertices:
        return

    click_game_vertex(app, illegal_vertices[0])

    assert app.staged_cop_destinations == []


def test_staged_multicop_buffer_resets_on_restart() -> None:
    app = CopsAndRobbersApp(seed=123)
    app.setup_cop_count = 2
    app.start_new_game(6, 7, 10)
    app._start_on_selected_positions((0, 1), 3)

    click_game_vertex(app, 0)
    app.restart_current_graph()

    assert app.staged_cop_destinations == []


def test_bot_robber_starts_after_human_cop_placement() -> None:
    app = CopsAndRobbersApp(seed=123)
    app.setup_cop_count = 2
    app.game_mode = GameMode.PLAYER_COP_VS_BOT_ROBBER
    app.bot_level = BotLevel.RANDOM
    app.start_new_game(6, 7, 10)

    click_vertex(app, 0)
    click_vertex(app, 1)

    assert app.current_screen is AppScreen.GAME
    assert app.state is not None
    assert app.state.cop_positions == (0, 1)
    assert app.state.robber_position not in app.state.cop_positions


def test_bot_cop_auto_places_then_waits_for_human_robber() -> None:
    app = CopsAndRobbersApp(seed=123)
    app.setup_cop_count = 3
    app.game_mode = GameMode.BOT_COP_VS_PLAYER_ROBBER
    app.bot_level = BotLevel.EASY
    app.start_new_game(6, 7, 10)

    assert app.current_screen is AppScreen.PLACEMENT
    assert len(app.selected_cop_positions) == 3

    robber_candidate = next(
        vertex for vertex in app.graph.vertices()
        if vertex not in app.selected_cop_positions
    )
    click_vertex(app, robber_candidate)

    assert app.current_screen is AppScreen.GAME
    assert app.state is not None
    assert app.state.cop_count == 3


def test_bot_turn_applies_legal_move() -> None:
    app = CopsAndRobbersApp(seed=123)
    app.setup_cop_count = 2
    app.game_mode = GameMode.BOT_COP_VS_PLAYER_ROBBER
    app.bot_level = BotLevel.RANDOM
    app.start_new_game(6, 7, 10)
    robber_candidate = next(
        vertex for vertex in app.graph.vertices()
        if vertex not in app.selected_cop_positions
    )
    click_vertex(app, robber_candidate)
    assert app.state is not None
    assert app.state.current_player is PlayerRole.COP

    app.last_bot_action_ms = -10_000
    app.update()

    assert app.state.current_player is PlayerRole.ROBBER or app.state.status.name == "COP_WIN"
    assert app.state.move_history


def test_expert_bot_level_resolves_to_minimax_and_rendered_label() -> None:
    app = CopsAndRobbersApp(seed=123)
    app.bot_level = BotLevel.EXPERT

    app.render()

    assert app._bot_label() == "5 Expert"


def test_bot_level_depth_adapts_to_cop_count() -> None:
    app = CopsAndRobbersApp(seed=123)
    app.bot_level = BotLevel.EXPERT
    app.setup_cop_count = 1

    assert app._bot_engine_for_state(None) == ("minimax", 5)

    app.setup_cop_count = 3

    assert app._bot_engine_for_state(None) == ("minimax", 3)


def test_bot_level_depth_clamps_for_large_root_branching() -> None:
    app = CopsAndRobbersApp(seed=123)
    app.bot_level = BotLevel.EXPERT
    app.setup_cop_count = 3
    app.start_new_game(10, 45, 10)
    app._start_on_selected_positions((0, 1, 2), 9)

    assert app._bot_engine_for_state(app.state)[1] <= 2
