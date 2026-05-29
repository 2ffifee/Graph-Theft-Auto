"""Main Pygame application."""

from __future__ import annotations

import os
import random
from enum import Enum

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from cops_and_robbers.core.game_rules import GameRules
from cops_and_robbers.core.game_state import GameState
from cops_and_robbers.core.graph_generator import generate_connected_graph
from cops_and_robbers.core.graph_model import GraphModel
from cops_and_robbers.core.player import PlayerRole
from cops_and_robbers.ui.graph_layout import GraphLayout
from cops_and_robbers.ui.input_handler import InputHandler
from cops_and_robbers.ui.renderer import Renderer
from cops_and_robbers.ui.widgets import Button, Stepper
from cops_and_robbers.utils.validation import (
    MAX_ROUNDS,
    MAX_VERTICES,
    MIN_ROUNDS,
    MIN_VERTICES,
    clamp,
    max_edges_for_vertices,
    validate_edge_count,
    validate_round_limit,
)


class AppScreen(Enum):
    SETUP = "setup"
    PLACEMENT = "placement"
    GAME = "game"


class CopsAndRobbersApp:
    WIDTH = 1100
    HEIGHT = 750
    MIN_COPS = 1
    MAX_COPS = 3

    def __init__(
        self,
        initial_n: int = 10,
        initial_m: int = 15,
        initial_rounds: int = 20,
        seed: int | None = None,
        start_immediately: bool = False,
    ):
        pygame.init()
        pygame.display.set_caption("Graph Theft Auto")
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(self.screen)
        self.input_handler = InputHandler()
        self.rules = GameRules()
        self.rng = random.Random(seed)
        self.seed = seed

        self.current_screen = AppScreen.SETUP
        self.running = True
        self.setup_n = clamp(initial_n, MIN_VERTICES, MAX_VERTICES)
        self.setup_m = clamp(initial_m, self.setup_n - 1, max_edges_for_vertices(self.setup_n))
        self.setup_rounds = clamp(initial_rounds, MIN_ROUNDS, MAX_ROUNDS)
        self.setup_cop_count = 1
        self.setup_error: str | None = None

        self.graph: GraphModel | None = None
        self.state: GameState | None = None
        self.layout: GraphLayout | None = None
        self.selected_cop_positions: list[int] = []

        self.board_rect = pygame.Rect(20, 76, 790, 650)
        self.panel_rect = pygame.Rect(830, 76, 250, 650)

        if start_immediately:
            self.start_new_game(self.setup_n, self.setup_m, self.setup_rounds)

    def run(self) -> None:
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            self.render()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

    def start_new_game(self, n: int, m: int, round_limit: int) -> None:
        validate_edge_count(n, m)
        validate_round_limit(round_limit)
        self.setup_n = n
        self.setup_m = m
        self.setup_rounds = round_limit
        self.graph = generate_connected_graph(n, m, seed=self._next_seed())
        self._begin_placement_on_graph(self.graph)

    def restart_current_graph(self) -> None:
        if self.graph is None:
            return
        self._begin_placement_on_graph(self.graph)

    def generate_new_graph(self) -> None:
        self.start_new_game(self.setup_n, self.setup_m, self.setup_rounds)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.KEYDOWN:
            self._handle_key(event.key)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.current_screen is AppScreen.SETUP:
                self._handle_setup_click(event.pos)
            elif self.current_screen is AppScreen.PLACEMENT:
                self._handle_placement_click(event.pos)
            else:
                self._handle_game_click(event.pos)

    def render(self) -> None:
        if self.current_screen is AppScreen.SETUP:
            self.renderer.draw_setup(
                self._setup_steppers(),
                self._setup_buttons(),
                "Mode: Player vs Player",
                self.setup_error,
            )
            return

        if self.current_screen is AppScreen.PLACEMENT:
            if self.graph is None or self.layout is None:
                return
            self.renderer.draw_placement(
                self.graph,
                self.layout,
                self.board_rect,
                self.panel_rect,
                self._placement_buttons(),
                self.setup_rounds,
                tuple(self.selected_cop_positions),
                self.setup_cop_count,
            )
            return

        if self.state is None or self.layout is None:
            return

        self.renderer.draw_game(
            self.state,
            self.layout,
            self.rules,
            self.board_rect,
            self.panel_rect,
            self._game_buttons(),
        )

    def _begin_placement_on_graph(self, graph: GraphModel) -> None:
        self.state = None
        self.selected_cop_positions = []
        self.layout = GraphLayout(
            graph,
            self.board_rect.width,
            self.board_rect.height,
            origin=(self.board_rect.x, self.board_rect.y),
        )
        self.current_screen = AppScreen.PLACEMENT
        self.setup_error = None

    def _start_on_selected_positions(self, cop_positions: tuple[int, ...], robber_position: int) -> None:
        if self.graph is None:
            return
        self.state = GameState(
            graph=self.graph,
            cop_positions=cop_positions,
            robber_position=robber_position,
            round_limit=self.setup_rounds,
        )
        self.selected_cop_positions = []
        self.current_screen = AppScreen.GAME
        self.setup_error = None

    def _handle_key(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_r and self.current_screen in {AppScreen.PLACEMENT, AppScreen.GAME}:
            self.restart_current_graph()
        elif key == pygame.K_n and self.current_screen in {AppScreen.PLACEMENT, AppScreen.GAME}:
            self.generate_new_graph()

    def _handle_setup_click(self, pos: tuple[int, int]) -> None:
        buttons = self._setup_buttons()
        action = self.input_handler.clicked_button(pos, buttons)
        if action is None:
            for stepper in self._setup_steppers():
                action = self.input_handler.clicked_button(pos, list(stepper.make_buttons(75, self._stepper_y(stepper.label))))
                if action is not None:
                    break
        if action is None:
            return
        self._perform_setup_action(action)

    def _handle_placement_click(self, pos: tuple[int, int]) -> None:
        action = self.input_handler.clicked_button(pos, self._placement_buttons())
        if action == "restart":
            self.restart_current_graph()
            return
        if action == "new_graph":
            self.generate_new_graph()
            return
        if action == "setup":
            self.current_screen = AppScreen.SETUP
            return

        vertex = self.input_handler.clicked_vertex(pos, self.board_rect, self.layout)
        if vertex is None:
            return
        if len(self.selected_cop_positions) < self.setup_cop_count:
            if vertex in self.selected_cop_positions:
                return
            self.selected_cop_positions.append(vertex)
            return
        if vertex in self.selected_cop_positions:
            return
        self._start_on_selected_positions(tuple(self.selected_cop_positions), vertex)

    def _handle_game_click(self, pos: tuple[int, int]) -> None:
        action = self.input_handler.clicked_button(pos, self._game_buttons())
        if action == "restart":
            self.restart_current_graph()
            return
        if action == "new_graph":
            self.generate_new_graph()
            return
        if action == "setup":
            self.current_screen = AppScreen.SETUP
            return

        if self.state is None:
            return
        if self.state.cop_count > 1 and self.state.current_player is PlayerRole.COP:
            return
        vertex = self.input_handler.clicked_vertex(pos, self.board_rect, self.layout)
        if vertex is None or not self.rules.is_legal_move(self.state, vertex):
            return
        self.rules.apply_move(self.state, vertex)

    def _perform_setup_action(self, action: str) -> None:
        if action == "n_minus":
            self.setup_n = clamp(self.setup_n - 1, MIN_VERTICES, MAX_VERTICES)
            self._clamp_edges_for_current_n()
        elif action == "n_plus":
            self.setup_n = clamp(self.setup_n + 1, MIN_VERTICES, MAX_VERTICES)
            self._clamp_edges_for_current_n()
        elif action == "m_minus":
            self.setup_m = clamp(self.setup_m - 1, self.setup_n - 1, max_edges_for_vertices(self.setup_n))
        elif action == "m_plus":
            self.setup_m = clamp(self.setup_m + 1, self.setup_n - 1, max_edges_for_vertices(self.setup_n))
        elif action == "rounds_minus":
            self.setup_rounds = clamp(self.setup_rounds - 1, MIN_ROUNDS, MAX_ROUNDS)
        elif action == "rounds_plus":
            self.setup_rounds = clamp(self.setup_rounds + 1, MIN_ROUNDS, MAX_ROUNDS)
        elif action == "cops_minus":
            self.setup_cop_count = clamp(self.setup_cop_count - 1, self.MIN_COPS, self.MAX_COPS)
        elif action == "cops_plus":
            self.setup_cop_count = clamp(self.setup_cop_count + 1, self.MIN_COPS, self.MAX_COPS)
        elif action == "start":
            try:
                self.start_new_game(self.setup_n, self.setup_m, self.setup_rounds)
            except ValueError as exc:
                self.setup_error = str(exc)

    def _clamp_edges_for_current_n(self) -> None:
        self.setup_m = clamp(self.setup_m, self.setup_n - 1, max_edges_for_vertices(self.setup_n))

    def _setup_steppers(self) -> list[Stepper]:
        return [
            Stepper("Vertices n:", self.setup_n, "n_minus", "n_plus", MIN_VERTICES, MAX_VERTICES),
            Stepper(
                "Edges m:",
                self.setup_m,
                "m_minus",
                "m_plus",
                self.setup_n - 1,
                max_edges_for_vertices(self.setup_n),
            ),
            Stepper("Rounds T:", self.setup_rounds, "rounds_minus", "rounds_plus", MIN_ROUNDS, MAX_ROUNDS),
            Stepper("Cops:", self.setup_cop_count, "cops_minus", "cops_plus", self.MIN_COPS, self.MAX_COPS),
        ]

    def _setup_buttons(self) -> list[Button]:
        return [Button(pygame.Rect(75, 344, 165, 36), "Start Game", "start")]

    def _game_buttons(self) -> list[Button]:
        return [
            Button(pygame.Rect(852, 392, 205, 38), "New Graph", "new_graph"),
            Button(pygame.Rect(852, 442, 205, 38), "Restart", "restart"),
            Button(pygame.Rect(852, 492, 205, 38), "Setup", "setup"),
        ]

    def _placement_buttons(self) -> list[Button]:
        return [
            Button(pygame.Rect(852, 392, 205, 38), "New Graph", "new_graph"),
            Button(pygame.Rect(852, 442, 205, 38), "Clear Choice", "restart"),
            Button(pygame.Rect(852, 492, 205, 38), "Setup", "setup"),
        ]

    def _stepper_y(self, label: str) -> int:
        lookup = {"Vertices n:": 135, "Edges m:": 189, "Rounds T:": 243, "Cops:": 297}
        return lookup[label]

    def _next_seed(self) -> int:
        return self.rng.randrange(0, 2**32)
