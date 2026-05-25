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
        option_rows: list[tuple[str, str]],
        error: str | None,
    ) -> None:
        self.clear()
        title = self.title_font.render("Graph Theft Auto", True, colors.TEXT)
        self.surface.blit(title, (40, 40))

        panel = pygame.Rect(40, 105, 490, 430)
        pygame.draw.rect(self.surface, colors.PANEL_BG, panel, border_radius=8)
        pygame.draw.rect(self.surface, colors.PANEL_BORDER, panel, width=1, border_radius=8)

        y = 135
        for stepper in steppers:
            stepper.draw(self.surface, self.font, 75, y)
            y += 54

        option_y = 363
        for label, value in option_rows:
            label_surface = self.font.render(label, True, colors.TEXT)
            self.surface.blit(label_surface, (75, option_y + 5))
            value_rect = pygame.Rect(246, option_y, 205, 30)
            pygame.draw.rect(self.surface, colors.VERTEX, value_rect, border_radius=4)
            pygame.draw.rect(self.surface, colors.PANEL_BORDER, value_rect, width=1, border_radius=4)
            value_surface = self.small_font.render(value, True, colors.TEXT)
            self.surface.blit(value_surface, value_surface.get_rect(center=value_rect.center))
            option_y += 48

        for button in buttons:
            button.draw(self.surface, self.font)

        if error:
            err = self.small_font.render(error, True, colors.ERROR)
            self.surface.blit(err, (75, 512))

    def draw_game(
        self,
        state: GameState,
        layout: GraphLayout,
        rules: GameRules,
        board_rect: pygame.Rect,
        panel_rect: pygame.Rect,
        buttons: list[Button],
        mode_label: str,
        bot_label: str,
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
        self._draw_panel(state, layout, panel_rect, buttons, mode_label, bot_label)

    def draw_placement(
        self,
        graph: GraphModel,
        layout: GraphLayout,
        board_rect: pygame.Rect,
        panel_rect: pygame.Rect,
        buttons: list[Button],
        round_limit: int,
        selected_cop_position: int | None,
        mode_label: str,
        bot_label: str,
    ) -> None:
        self.clear()
        title = self.title_font.render("Graph Theft Auto", True, colors.TEXT)
        self.surface.blit(title, (20, 18))

        pygame.draw.rect(self.surface, (250, 250, 250), board_rect, border_radius=8)
        pygame.draw.rect(self.surface, colors.PANEL_BORDER, board_rect, width=1, border_radius=8)
        pygame.draw.rect(self.surface, colors.PANEL_BG, panel_rect, border_radius=8)
        pygame.draw.rect(self.surface, colors.PANEL_BORDER, panel_rect, width=1, border_radius=8)

        selectable = set(graph.vertices())
        if selected_cop_position is not None:
            selectable.remove(selected_cop_position)
        self._draw_placement_graph(graph, layout, selectable, selected_cop_position)
        self._draw_placement_panel(
            graph,
            layout,
            panel_rect,
            buttons,
            round_limit,
            selected_cop_position,
            mode_label,
            bot_label,
        )

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
        cop_pos = positions[state.cop_position]
        robber_pos = positions[state.robber_position]
        if state.cop_position == state.robber_position:
            self._draw_cop_car(cop_pos, scale=0.9)
            self._draw_robber_marker((cop_pos[0] + 20, cop_pos[1] + 14), scale=0.9)
            return

        self._draw_cop_car((cop_pos[0] - 12, cop_pos[1] - 19), scale=0.86)
        self._draw_robber_marker((robber_pos[0] + 14, robber_pos[1] - 18), scale=0.95)

    def _draw_placement_graph(
        self,
        graph: GraphModel,
        layout: GraphLayout,
        selectable: set[int],
        selected_cop_position: int | None,
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

        if selected_cop_position is not None:
            cop_pos = positions[selected_cop_position]
            self._draw_cop_car((cop_pos[0] - 12, cop_pos[1] - 19), scale=0.82)

    def _draw_cop_car(self, center: tuple[float, float], scale: float = 1.0) -> None:
        x, y = center
        body = pygame.Rect(0, 0, int(34 * scale), int(18 * scale))
        body.center = (round(x), round(y))
        roof = pygame.Rect(0, 0, int(17 * scale), int(10 * scale))
        roof.center = (round(x), round(y - 7 * scale))
        wheel_radius = max(2, round(3 * scale))

        pygame.draw.rect(self.surface, (245, 248, 255), body, border_radius=round(4 * scale))
        pygame.draw.rect(self.surface, colors.COP, body, width=max(1, round(2 * scale)), border_radius=round(4 * scale))
        pygame.draw.rect(self.surface, (180, 220, 255), roof, border_radius=round(3 * scale))
        pygame.draw.rect(self.surface, colors.VERTEX_OUTLINE, body, width=1, border_radius=round(4 * scale))
        pygame.draw.circle(self.surface, colors.VERTEX_OUTLINE, (body.left + round(8 * scale), body.bottom), wheel_radius)
        pygame.draw.circle(self.surface, colors.VERTEX_OUTLINE, (body.right - round(8 * scale), body.bottom), wheel_radius)
        pygame.draw.circle(self.surface, (230, 50, 50), (round(x - 4 * scale), roof.top), max(2, round(2 * scale)))
        pygame.draw.circle(self.surface, colors.COP, (round(x + 4 * scale), roof.top), max(2, round(2 * scale)))

    def _draw_robber_marker(self, center: tuple[float, float], scale: float = 1.0) -> None:
        x, y = center
        self._draw_stolen_car((x + 8 * scale, y + 10 * scale), scale * 0.72)
        self._draw_black_clad_robber((x - 8 * scale, y - 2 * scale), scale)

    def _draw_stolen_car(self, center: tuple[float, float], scale: float = 1.0) -> None:
        x, y = center
        body = pygame.Rect(0, 0, int(32 * scale), int(15 * scale))
        body.center = (round(x), round(y))
        roof = pygame.Rect(0, 0, int(15 * scale), int(8 * scale))
        roof.center = (round(x + 2 * scale), round(y - 6 * scale))
        wheel_radius = max(2, round(3 * scale))

        pygame.draw.rect(self.surface, (32, 34, 38), body, border_radius=round(4 * scale))
        pygame.draw.rect(self.surface, (75, 78, 86), roof, border_radius=round(3 * scale))
        pygame.draw.rect(self.surface, (12, 12, 14), body, width=1, border_radius=round(4 * scale))
        pygame.draw.circle(self.surface, (235, 215, 80), (body.left + round(3 * scale), body.centery), max(1, round(1.5 * scale)))
        pygame.draw.circle(self.surface, colors.ROBBER, (body.right - round(3 * scale), body.centery), max(1, round(1.5 * scale)))
        pygame.draw.circle(self.surface, colors.VERTEX_OUTLINE, (body.left + round(8 * scale), body.bottom), wheel_radius)
        pygame.draw.circle(self.surface, colors.VERTEX_OUTLINE, (body.right - round(8 * scale), body.bottom), wheel_radius)

    def _draw_black_clad_robber(self, center: tuple[float, float], scale: float = 1.0) -> None:
        x, y = center
        outline = (245, 245, 245)
        black = (8, 8, 10)
        dark = (20, 20, 24)
        gray = (52, 52, 58)
        head_radius = max(5, round(7 * scale))
        head_center = (round(x), round(y - 13 * scale))
        torso = pygame.Rect(0, 0, max(8, int(13 * scale)), max(13, int(18 * scale)))
        torso.center = (round(x), round(y + 4 * scale))
        arm_y = round(y + 2 * scale)
        leg_top = round(y + 13 * scale)

        pygame.draw.circle(self.surface, outline, head_center, head_radius + 1)
        pygame.draw.rect(self.surface, outline, torso.inflate(2, 2), border_radius=round(4 * scale))
        pygame.draw.line(
            self.surface,
            outline,
            (round(x - 7 * scale), arm_y),
            (round(x - 15 * scale), round(y + 11 * scale)),
            width=max(2, round(4 * scale)),
        )
        pygame.draw.line(
            self.surface,
            outline,
            (round(x + 7 * scale), arm_y),
            (round(x + 13 * scale), round(y + 9 * scale)),
            width=max(2, round(4 * scale)),
        )
        pygame.draw.line(
            self.surface,
            outline,
            (round(x - 3 * scale), leg_top),
            (round(x - 9 * scale), round(y + 24 * scale)),
            width=max(2, round(4 * scale)),
        )
        pygame.draw.line(
            self.surface,
            outline,
            (round(x + 3 * scale), leg_top),
            (round(x + 9 * scale), round(y + 24 * scale)),
            width=max(2, round(4 * scale)),
        )

        pygame.draw.circle(self.surface, black, head_center, head_radius)
        pygame.draw.rect(self.surface, dark, torso, border_radius=round(4 * scale))
        pygame.draw.line(
            self.surface,
            black,
            (round(x - 7 * scale), arm_y),
            (round(x - 15 * scale), round(y + 11 * scale)),
            width=max(1, round(2.5 * scale)),
        )
        pygame.draw.line(
            self.surface,
            black,
            (round(x + 7 * scale), arm_y),
            (round(x + 13 * scale), round(y + 9 * scale)),
            width=max(1, round(2.5 * scale)),
        )
        pygame.draw.line(
            self.surface,
            black,
            (round(x - 3 * scale), leg_top),
            (round(x - 9 * scale), round(y + 24 * scale)),
            width=max(1, round(2.5 * scale)),
        )
        pygame.draw.line(
            self.surface,
            black,
            (round(x + 3 * scale), leg_top),
            (round(x + 9 * scale), round(y + 24 * scale)),
            width=max(1, round(2.5 * scale)),
        )

        eye_y = head_center[1] - round(1 * scale)
        eye_band = pygame.Rect(round(x - 6 * scale), eye_y - 2, max(7, round(12 * scale)), max(3, round(4 * scale)))
        pygame.draw.rect(self.surface, gray, eye_band, border_radius=round(2 * scale))
        pygame.draw.circle(self.surface, (245, 245, 245), (head_center[0] - round(2 * scale), eye_y), max(1, round(1.2 * scale)))
        pygame.draw.circle(self.surface, (245, 245, 245), (head_center[0] + round(2 * scale), eye_y), max(1, round(1.2 * scale)))

    def _draw_panel(
        self,
        state: GameState,
        layout: GraphLayout,
        panel_rect: pygame.Rect,
        buttons: list[Button],
        mode_label: str,
        bot_label: str,
    ) -> None:
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
            f"cop: {state.cop_position}",
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

        layout_label = "planar" if layout.layout_method == "planar" else "low-crossing"
        for line in [
            f"mode: {mode_label}",
            f"bot: {bot_label}",
            f"layout: {layout_label}",
            f"crossings: {layout.edge_crossings}",
        ]:
            text = self.small_font.render(line, True, colors.MUTED_TEXT)
            self.surface.blit(text, (x, y))
            y += 22

        y = self._hint_y(y + 12, buttons)
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
        layout: GraphLayout,
        panel_rect: pygame.Rect,
        buttons: list[Button],
        round_limit: int,
        selected_cop_position: int | None,
        mode_label: str,
        bot_label: str,
    ) -> None:
        x = panel_rect.x + 22
        y = panel_rect.y + 22
        heading = self.heading_font.render("Start Positions", True, colors.TEXT)
        self.surface.blit(heading, (x, y))
        y += 42

        prompt = "Cop: choose a vertex" if selected_cop_position is None else "Robber: choose a vertex"
        lines = [
            f"n: {graph.n}",
            f"m: {graph.edge_count}",
            f"round limit: {round_limit}",
            prompt,
            f"cop: {selected_cop_position if selected_cop_position is not None else '-'}",
            "robber: -",
        ]
        for line in lines:
            color = colors.COP if line.startswith("Cop:") else colors.TEXT
            if line.startswith("Robber:"):
                color = colors.ROBBER
            text = self.font.render(line, True, color)
            self.surface.blit(text, (x, y))
            y += 29

        for line in [f"mode: {mode_label}", f"bot: {bot_label}"]:
            text = self.small_font.render(line, True, colors.MUTED_TEXT)
            self.surface.blit(text, (x, y))
            y += 22

        layout_label = "planar" if layout.layout_method == "planar" else "low-crossing"
        for line in [f"layout: {layout_label}", f"crossings: {layout.edge_crossings}"]:
            text = self.small_font.render(line, True, colors.MUTED_TEXT)
            self.surface.blit(text, (x, y))
            y += 22

        y = self._hint_y(y + 12, buttons)
        hint_lines = ["Click highlighted vertices.", "Cop and robber must differ."]
        for line in hint_lines:
            text = self.small_font.render(line, True, colors.MUTED_TEXT)
            self.surface.blit(text, (x, y))
            y += 22

        for button in buttons:
            button.draw(self.surface, self.font)

    def _hint_y(self, preferred_y: int, buttons: list[Button]) -> int:
        if not buttons:
            return preferred_y
        first_button_y = min(button.rect.y for button in buttons)
        return min(preferred_y, first_button_y - 58)
