"""Pygame rendering for setup and game screens."""

from __future__ import annotations

import pygame

from cops_and_robbers.core.game_rules import GameRules
from cops_and_robbers.core.game_state import GameState, GameStatus
from cops_and_robbers.core.graph_model import GraphModel
from cops_and_robbers.ui import colors
from cops_and_robbers.ui.graph_layout import GraphLayout
from cops_and_robbers.ui.widgets import Button, Stepper


class Renderer:
    VERTEX_RADIUS = 22

    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.title_font = pygame.font.SysFont("arial", 28, bold=True)
        self.heading_font = pygame.font.SysFont("arial", 22, bold=True)
        self.font = pygame.font.SysFont("arial", 18)
        self.small_font = pygame.font.SysFont("arial", 15)

    def clear(self) -> None:
        self.surface.fill(colors.BACKGROUND)

    def draw_setup(
        self,
        steppers: list[Stepper],
        buttons: list[Button],
        message: str | None,
        error: str | None,
    ) -> None:
        self.clear()
        title = self.title_font.render("Graph Theft Auto", True, colors.TEXT)
        self.surface.blit(title, (40, 40))

        panel = pygame.Rect(40, 105, 410, 320)
        pygame.draw.rect(self.surface, colors.PANEL_BG, panel, border_radius=8)
        pygame.draw.rect(self.surface, colors.PANEL_BORDER, panel, width=1, border_radius=8)

        y = 135
        for stepper in steppers:
            stepper.draw(self.surface, self.font, 75, y)
            y += 54

        for button in buttons:
            button.draw(self.surface, self.font)

        if message:
            msg = self.small_font.render(message, True, colors.MUTED_TEXT)
            self.surface.blit(msg, (75, 386))
        if error:
            err = self.small_font.render(error, True, colors.ERROR)
            self.surface.blit(err, (75, 406))

    def draw_game(
        self,
        state: GameState,
        layout: GraphLayout,
        rules: GameRules,
        board_rect: pygame.Rect,
        panel_rect: pygame.Rect,
        buttons: list[Button],
    ) -> None:
        self.clear()
        title = self.title_font.render("Graph Theft Auto", True, colors.TEXT)
        self.surface.blit(title, (20, 18))

        pygame.draw.rect(self.surface, (250, 250, 250), board_rect, border_radius=8)
        pygame.draw.rect(self.surface, colors.PANEL_BORDER, board_rect, width=1, border_radius=8)
        pygame.draw.rect(self.surface, colors.PANEL_BG, panel_rect, border_radius=8)
        pygame.draw.rect(self.surface, colors.PANEL_BORDER, panel_rect, width=1, border_radius=8)

        legal_moves = set(rules.get_legal_moves(state))
        self._draw_graph(state, layout, legal_moves)
        self._draw_panel(state, panel_rect, buttons)

    def draw_placement(
        self,
        graph: GraphModel,
        layout: GraphLayout,
        board_rect: pygame.Rect,
        panel_rect: pygame.Rect,
        buttons: list[Button],
        round_limit: int,
        selected_cop_positions: tuple[int, ...],
        cop_count: int,
    ) -> None:
        self.clear()
        title = self.title_font.render("Graph Theft Auto", True, colors.TEXT)
        self.surface.blit(title, (20, 18))

        pygame.draw.rect(self.surface, (250, 250, 250), board_rect, border_radius=8)
        pygame.draw.rect(self.surface, colors.PANEL_BORDER, board_rect, width=1, border_radius=8)
        pygame.draw.rect(self.surface, colors.PANEL_BG, panel_rect, border_radius=8)
        pygame.draw.rect(self.surface, colors.PANEL_BORDER, panel_rect, width=1, border_radius=8)

        selectable = set(graph.vertices())
        selectable.difference_update(selected_cop_positions)
        self._draw_placement_graph(graph, layout, selectable, selected_cop_positions)
        self._draw_placement_panel(graph, panel_rect, buttons, round_limit, selected_cop_positions, cop_count)

    def _draw_graph(
        self,
        state: GameState,
        layout: GraphLayout,
        legal_moves: set[int],
    ) -> None:
        positions = layout.positions
        for u, v in state.graph.edges():
            pygame.draw.line(self.surface, colors.EDGE, positions[u], positions[v], width=2)

        for vertex, pos in positions.items():
            if vertex in legal_moves:
                pygame.draw.circle(self.surface, colors.LEGAL_MOVE, pos, self.VERTEX_RADIUS + 7)
                pygame.draw.circle(
                    self.surface,
                    colors.LEGAL_MOVE_OUTLINE,
                    pos,
                    self.VERTEX_RADIUS + 7,
                    width=2,
                )
            pygame.draw.circle(self.surface, colors.VERTEX, pos, self.VERTEX_RADIUS)
            pygame.draw.circle(self.surface, colors.VERTEX_OUTLINE, pos, self.VERTEX_RADIUS, width=2)
            label = self.small_font.render(str(vertex), True, colors.TEXT)
            self.surface.blit(label, label.get_rect(center=pos))

        self._draw_tokens(state, positions)

    def _draw_tokens(self, state: GameState, positions: dict[int, tuple[float, float]]) -> None:
        robber_pos = positions[state.robber_position]
        for index, cop_position in enumerate(state.cop_positions, start=1):
            cop_pos = positions[cop_position]
            token_center = (cop_pos[0] - 12, cop_pos[1] - 18)
            pygame.draw.circle(self.surface, colors.COP, token_center, 11)
            label = self.small_font.render(str(index), True, (255, 255, 255))
            self.surface.blit(label, label.get_rect(center=token_center))
        pygame.draw.circle(self.surface, colors.ROBBER, (robber_pos[0] + 12, robber_pos[1] - 18), 10)

    def _draw_placement_graph(
        self,
        graph: GraphModel,
        layout: GraphLayout,
        selectable: set[int],
        selected_cop_positions: tuple[int, ...],
    ) -> None:
        positions = layout.positions
        for u, v in graph.edges():
            pygame.draw.line(self.surface, colors.EDGE, positions[u], positions[v], width=2)

        for vertex, pos in positions.items():
            if vertex in selectable:
                pygame.draw.circle(self.surface, colors.LEGAL_MOVE, pos, self.VERTEX_RADIUS + 7)
                pygame.draw.circle(
                    self.surface,
                    colors.LEGAL_MOVE_OUTLINE,
                    pos,
                    self.VERTEX_RADIUS + 7,
                    width=2,
                )
            pygame.draw.circle(self.surface, colors.VERTEX, pos, self.VERTEX_RADIUS)
            pygame.draw.circle(self.surface, colors.VERTEX_OUTLINE, pos, self.VERTEX_RADIUS, width=2)
            label = self.small_font.render(str(vertex), True, colors.TEXT)
            self.surface.blit(label, label.get_rect(center=pos))

        for index, selected_cop_position in enumerate(selected_cop_positions, start=1):
            cop_pos = positions[selected_cop_position]
            token_center = (cop_pos[0] - 12, cop_pos[1] - 18)
            pygame.draw.circle(self.surface, colors.COP, token_center, 11)
            label = self.small_font.render(str(index), True, (255, 255, 255))
            self.surface.blit(label, label.get_rect(center=token_center))

    def _draw_panel(self, state: GameState, panel_rect: pygame.Rect, buttons: list[Button]) -> None:
        x = panel_rect.x + 22
        y = panel_rect.y + 22
        heading = self.heading_font.render("Status", True, colors.TEXT)
        self.surface.blit(heading, (x, y))
        y += 42

        lines = [
            f"n: {state.graph.n}",
            f"m: {state.graph.edge_count}",
            f"round: {state.current_round} / {state.round_limit}",
            f"player: {state.current_player.label}",
            f"status: {state.status.label}",
            f"cops: {', '.join(str(vertex) for vertex in state.cop_positions)}",
            f"robber: {state.robber_position}",
        ]
        if state.status is GameStatus.COP_WIN:
            status_color = colors.COP
        elif state.status is GameStatus.ROBBER_WIN:
            status_color = colors.ROBBER
        else:
            status_color = colors.TEXT

        for line in lines:
            color = status_color if line.startswith("status:") else colors.TEXT
            text = self.font.render(line, True, color)
            self.surface.blit(text, (x, y))
            y += 29

        y += 12
        hint_lines = ["Click highlighted vertices.", "R: restart   N: new graph"]
        for line in hint_lines:
            text = self.small_font.render(line, True, colors.MUTED_TEXT)
            self.surface.blit(text, (x, y))
            y += 22

        for button in buttons:
            button.draw(self.surface, self.font)

    def _draw_placement_panel(
        self,
        graph: GraphModel,
        panel_rect: pygame.Rect,
        buttons: list[Button],
        round_limit: int,
        selected_cop_positions: tuple[int, ...],
        cop_count: int,
    ) -> None:
        x = panel_rect.x + 22
        y = panel_rect.y + 22
        heading = self.heading_font.render("Start Positions", True, colors.TEXT)
        self.surface.blit(heading, (x, y))
        y += 42

        if len(selected_cop_positions) < cop_count:
            prompt = f"Cop {len(selected_cop_positions) + 1}: choose a vertex"
        else:
            prompt = "Robber: choose a vertex"
        selected_label = ", ".join(str(vertex) for vertex in selected_cop_positions) or "-"
        lines = [
            f"n: {graph.n}",
            f"m: {graph.edge_count}",
            f"round limit: {round_limit}",
            f"cops: {cop_count}",
            "mode: Player vs Player",
            prompt,
            f"cop starts: {selected_label}",
            "robber: -",
        ]
        for line in lines:
            color = colors.COP if line.startswith("Cop ") else colors.TEXT
            if line.startswith("Robber:"):
                color = colors.ROBBER
            text = self.font.render(line, True, color)
            self.surface.blit(text, (x, y))
            y += 29

        y += 12
        hint_lines = ["Click highlighted vertices.", "Cop and robber must differ."]
        for line in hint_lines:
            text = self.small_font.render(line, True, colors.MUTED_TEXT)
            self.surface.blit(text, (x, y))
            y += 22

        for button in buttons:
            button.draw(self.surface, self.font)
