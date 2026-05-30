"""Main Pygame application."""

from __future__ import annotations

import os
import random
from enum import Enum

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from cops_and_robbers.bots.bot_base import BotBase
from cops_and_robbers.bots.greedy_bot import GreedyBot
from cops_and_robbers.bots.minimax_bot import MinimaxBot
from cops_and_robbers.bots.random_bot import RandomBot
from cops_and_robbers.core.game_rules import GameRules
from cops_and_robbers.core.game_state import GameState, GameStatus
from cops_and_robbers.core.graph_generator import generate_connected_graph
from cops_and_robbers.core.graph_model import GraphModel
from cops_and_robbers.core.move import Move
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


class GameMode(Enum):
    PLAYER_VS_PLAYER = "Player vs Player"
    PLAYER_COP_VS_BOT_ROBBER = "Player Cop vs Bot Robber"
    BOT_COP_VS_PLAYER_ROBBER = "Bot Cop vs Player Robber"
    BOT_VS_BOT = "Bot vs Bot"


class BotKind(Enum):
    RANDOM = "Random"
    GREEDY = "Greedy"
    MINIMAX = "Minimax"


class CopsAndRobbersApp:
    WIDTH = 1100
    HEIGHT = 750
    MIN_COPS = 1
    MAX_COPS = 3
    MIN_BOT_DEPTH = 1
    MAX_BOT_DEPTH = 5

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
        self.setup_bot_depth = 3
        self.game_mode = GameMode.PLAYER_VS_PLAYER
        self.bot_kind = BotKind.GREEDY
        self.setup_error: str | None = None

        self.graph: GraphModel | None = None
        self.state: GameState | None = None
        self.layout: GraphLayout | None = None
        self.selected_cop_positions: list[int] = []
        self.staged_cop_destinations: list[int] = []

        self.board_rect = pygame.Rect(20, 76, 790, 650)
        self.panel_rect = pygame.Rect(830, 76, 250, 650)
        self.last_bot_action_ms = 0
        self.bot_move_delay_ms = 300

        if start_immediately:
            self.start_new_game(self.setup_n, self.setup_m, self.setup_rounds)

    def run(self) -> None:
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            self.update()
            self.render()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

    def update(self) -> None:
        if self.current_screen is AppScreen.GAME:
            self._apply_bot_turn_if_ready()

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
                self._setup_option_rows(),
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
                self.game_mode.value,
                self._bot_label(),
            )
            return

        if self.state is None or self.layout is None:
            return

        legal_vertices: set[int] | None = None
        move_prompt: str | None = None
        if self._is_staged_cop_turn():
            current_cop_index = len(self.staged_cop_destinations)
            legal_vertices = set(self.rules.get_legal_cop_destinations(self.state, current_cop_index))
            move_prompt = f"moving: Cop {current_cop_index + 1} of {self.state.cop_count}"

        self.renderer.draw_game(
            self.state,
            self.layout,
            self.rules,
            self.board_rect,
            self.panel_rect,
            self._game_buttons(),
            legal_vertices,
            move_prompt,
            tuple(self.staged_cop_destinations),
            self.game_mode.value,
            self._bot_label(),
        )

    def _begin_placement_on_graph(self, graph: GraphModel) -> None:
        self.state = None
        self.selected_cop_positions = []
        self.staged_cop_destinations = []
        self.layout = GraphLayout(
            graph,
            self.board_rect.width,
            self.board_rect.height,
            origin=(self.board_rect.x, self.board_rect.y),
        )
        self.current_screen = AppScreen.PLACEMENT
        self.setup_error = None
        self._advance_bot_placement()

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
        self.staged_cop_destinations = []
        self.current_screen = AppScreen.GAME
        self.setup_error = None
        self.last_bot_action_ms = pygame.time.get_ticks()

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
            self.staged_cop_destinations = []
            self.current_screen = AppScreen.SETUP
            return

        vertex = self.input_handler.clicked_vertex(pos, self.board_rect, self.layout)
        if vertex is None:
            return
        if len(self.selected_cop_positions) < self.setup_cop_count:
            if self._is_bot_role(PlayerRole.COP):
                return
            if vertex in self.selected_cop_positions:
                return
            self.selected_cop_positions.append(vertex)
            self._advance_bot_placement()
            return
        if vertex in self.selected_cop_positions:
            return
        if self._is_bot_role(PlayerRole.ROBBER):
            return
        self._start_on_selected_positions(tuple(self.selected_cop_positions), vertex)

    def _handle_game_click(self, pos: tuple[int, int]) -> None:
        action = self.input_handler.clicked_button(pos, self._game_buttons())
        if action == "restart":
            self.staged_cop_destinations = []
            self.restart_current_graph()
            return
        if action == "new_graph":
            self.staged_cop_destinations = []
            self.generate_new_graph()
            return
        if action == "setup":
            self.staged_cop_destinations = []
            self.current_screen = AppScreen.SETUP
            return

        if self.state is None:
            return
        if self._is_bot_role(self.state.current_player):
            return
        if self._is_staged_cop_turn():
            self._handle_staged_cop_click(pos)
            return
        vertex = self.input_handler.clicked_vertex(pos, self.board_rect, self.layout)
        if vertex is None or not self.rules.is_legal_move(self.state, vertex):
            return
        self.rules.apply_move(self.state, vertex)
        self.staged_cop_destinations = []
        self.last_bot_action_ms = pygame.time.get_ticks()

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
        elif action == "depth_minus":
            self.setup_bot_depth = clamp(self.setup_bot_depth - 1, self.MIN_BOT_DEPTH, self.MAX_BOT_DEPTH)
        elif action == "depth_plus":
            self.setup_bot_depth = clamp(self.setup_bot_depth + 1, self.MIN_BOT_DEPTH, self.MAX_BOT_DEPTH)
        elif action == "mode_prev":
            self.game_mode = self._previous_enum_value(GameMode, self.game_mode)
        elif action == "mode_next":
            self.game_mode = self._next_enum_value(GameMode, self.game_mode)
        elif action == "bot_prev":
            self.bot_kind = self._previous_enum_value(BotKind, self.bot_kind)
        elif action == "bot_next":
            self.bot_kind = self._next_enum_value(BotKind, self.bot_kind)
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
            Stepper(
                "Bot depth:",
                self.setup_bot_depth,
                "depth_minus",
                "depth_plus",
                self.MIN_BOT_DEPTH,
                self.MAX_BOT_DEPTH,
            ),
        ]

    def _setup_buttons(self) -> list[Button]:
        return [
            Button(pygame.Rect(207, 413, 34, 30), "<", "mode_prev"),
            Button(pygame.Rect(455, 413, 34, 30), ">", "mode_next"),
            Button(pygame.Rect(207, 461, 34, 30), "<", "bot_prev"),
            Button(pygame.Rect(455, 461, 34, 30), ">", "bot_next"),
            Button(pygame.Rect(75, 524, 165, 36), "Start Game", "start"),
        ]

    def _setup_option_rows(self) -> list[tuple[str, str]]:
        return [
            ("Mode:", self.game_mode.value),
            ("Bot:", self._bot_label()),
        ]

    def _game_buttons(self) -> list[Button]:
        x = self.panel_rect.x + 22
        y = self.panel_rect.bottom - 180
        width = self.panel_rect.width - 44
        return [
            Button(pygame.Rect(x, y, width, 38), "New Graph", "new_graph"),
            Button(pygame.Rect(x, y + 50, width, 38), "Restart", "restart"),
            Button(pygame.Rect(x, y + 100, width, 38), "Setup", "setup"),
        ]

    def _placement_buttons(self) -> list[Button]:
        x = self.panel_rect.x + 22
        y = self.panel_rect.bottom - 180
        width = self.panel_rect.width - 44
        return [
            Button(pygame.Rect(x, y, width, 38), "New Graph", "new_graph"),
            Button(pygame.Rect(x, y + 50, width, 38), "Clear Choice", "restart"),
            Button(pygame.Rect(x, y + 100, width, 38), "Setup", "setup"),
        ]

    def _stepper_y(self, label: str) -> int:
        lookup = {
            "Vertices n:": 135,
            "Edges m:": 189,
            "Rounds T:": 243,
            "Cops:": 297,
            "Bot depth:": 351,
        }
        return lookup[label]

    def _next_seed(self) -> int:
        return self.rng.randrange(0, 2**32)

    def _is_staged_cop_turn(self) -> bool:
        return (
            self.state is not None
            and self.state.current_player is PlayerRole.COP
            and self.state.cop_count > 1
        )

    def _handle_staged_cop_click(self, pos: tuple[int, int]) -> None:
        if self.state is None:
            return
        current_cop_index = len(self.staged_cop_destinations)
        if current_cop_index >= self.state.cop_count:
            self.staged_cop_destinations = []
            return

        vertex = self.input_handler.clicked_vertex(pos, self.board_rect, self.layout)
        if vertex is None:
            return
        if vertex not in self.rules.get_legal_cop_destinations(self.state, current_cop_index):
            return

        self.staged_cop_destinations.append(vertex)
        if len(self.staged_cop_destinations) == self.state.cop_count:
            self.rules.apply_move(self.state, Move.cop(tuple(self.staged_cop_destinations)))
            self.staged_cop_destinations = []
            self.last_bot_action_ms = pygame.time.get_ticks()

    def _is_bot_role(self, role: PlayerRole) -> bool:
        if self.game_mode is GameMode.PLAYER_VS_PLAYER:
            return False
        if self.game_mode is GameMode.BOT_VS_BOT:
            return True
        if self.game_mode is GameMode.PLAYER_COP_VS_BOT_ROBBER:
            return role is PlayerRole.ROBBER
        if self.game_mode is GameMode.BOT_COP_VS_PLAYER_ROBBER:
            return role is PlayerRole.COP
        return False

    def _make_bot(self, role: PlayerRole) -> BotBase:
        seed = self._next_seed()
        if self.bot_kind is BotKind.RANDOM:
            return RandomBot(role=role, seed=seed)
        if self.bot_kind is BotKind.MINIMAX:
            return MinimaxBot(role=role, depth=self.setup_bot_depth, seed=seed)
        return GreedyBot(role=role, seed=seed)

    def _apply_bot_turn_if_ready(self) -> None:
        if self.state is None or self.state.status is not GameStatus.PLAYING:
            return
        if not self._is_bot_role(self.state.current_player):
            return

        now = pygame.time.get_ticks()
        if now - self.last_bot_action_ms < self.bot_move_delay_ms:
            return

        if self.state.current_player is PlayerRole.COP and self.state.cop_count > 1:
            legal_moves = self.rules.get_legal_cop_moves(self.state)
        else:
            legal_moves = self.rules.get_legal_moves(self.state)
        bot = self._make_bot(self.state.current_player)
        move = bot.choose_move(self.state, legal_moves)
        self.rules.apply_move(self.state, move)
        self.staged_cop_destinations = []
        self.last_bot_action_ms = now

    def _advance_bot_placement(self) -> None:
        if self.graph is None:
            return
        if self._is_bot_role(PlayerRole.COP):
            while len(self.selected_cop_positions) < self.setup_cop_count:
                position = self._choose_bot_cop_start()
                self.selected_cop_positions.append(position)

        if (
            len(self.selected_cop_positions) == self.setup_cop_count
            and self._is_bot_role(PlayerRole.ROBBER)
        ):
            robber_position = self._choose_bot_robber_start()
            self._start_on_selected_positions(tuple(self.selected_cop_positions), robber_position)

    def _choose_bot_cop_start(self) -> int:
        if self.graph is None:
            raise RuntimeError("cannot choose cop start without a graph")
        candidates = [
            vertex for vertex in self.graph.vertices()
            if vertex not in self.selected_cop_positions
        ]
        if self.bot_kind is BotKind.RANDOM:
            return self.rng.choice(candidates)
        scores = {
            vertex: (
                max(self.graph.shortest_distance(vertex, other) for other in self.graph.vertices()),
                -len(self.graph.neighbors(vertex)),
            )
            for vertex in candidates
        }
        best_score = min(scores.values())
        return self.rng.choice([vertex for vertex, score in scores.items() if score == best_score])

    def _choose_bot_robber_start(self) -> int:
        if self.graph is None:
            raise RuntimeError("cannot choose robber start without a graph")
        candidates = [
            vertex for vertex in self.graph.vertices()
            if vertex not in self.selected_cop_positions
        ]
        if self.bot_kind is BotKind.RANDOM:
            return self.rng.choice(candidates)
        scores = {
            vertex: (
                min(self.graph.shortest_distance(vertex, cop) for cop in self.selected_cop_positions),
                len(self.graph.neighbors(vertex)),
            )
            for vertex in candidates
        }
        best_score = max(scores.values())
        return self.rng.choice([vertex for vertex, score in scores.items() if score == best_score])

    def _next_enum_value(self, enum_type: type[Enum], current: Enum) -> Enum:
        values = list(enum_type)
        return values[(values.index(current) + 1) % len(values)]

    def _previous_enum_value(self, enum_type: type[Enum], current: Enum) -> Enum:
        values = list(enum_type)
        return values[(values.index(current) - 1) % len(values)]

    def _bot_label(self) -> str:
        if self.bot_kind is BotKind.MINIMAX:
            return f"Minimax d{self.setup_bot_depth}"
        return self.bot_kind.value
