import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from cops_and_robbers.ui.app import AppScreen, CopsAndRobbersApp


def click_vertex(app: CopsAndRobbersApp, vertex: int) -> None:
    assert app.layout is not None
    x, y = app.layout.positions[vertex]
    app._handle_placement_click((round(x), round(y)))


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
