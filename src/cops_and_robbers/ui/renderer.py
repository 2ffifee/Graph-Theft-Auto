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
    TITLE_FONT_SIZE = 28
    HEADING_FONT_SIZE = 22
    FONT_SIZE = 18
    SMALL_FONT_SIZE = 15

    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.scale = 1.0
        self.offset = (0, 0)
        self._font_scale = 0
        self.title_font = pygame.font.SysFont("arial", self.TITLE_FONT_SIZE, bold=True)
        self.heading_font = pygame.font.SysFont("arial", self.HEADING_FONT_SIZE, bold=True)
        self.font = pygame.font.SysFont("arial", self.FONT_SIZE)
        self.small_font = pygame.font.SysFont("arial", self.SMALL_FONT_SIZE)

    def set_viewport(self, scale: float, offset: tuple[int, int]) -> None:
        self.scale = scale
        self.offset = offset
        font_scale = max(1, round(scale * 100))
        if font_scale == self._font_scale:
            return
        self._font_scale = font_scale
        self.title_font = pygame.font.SysFont(
            "arial",
            max(1, round(self.TITLE_FONT_SIZE * scale)),
            bold=True,
        )
        self.heading_font = pygame.font.SysFont(
            "arial",
            max(1, round(self.HEADING_FONT_SIZE * scale)),
            bold=True,
        )
        self.font = pygame.font.SysFont("arial", max(1, round(self.FONT_SIZE * scale)))
        self.small_font = pygame.font.SysFont("arial", max(1, round(self.SMALL_FONT_SIZE * scale)))

    def clear(self) -> None:
        self.surface.fill(colors.BACKGROUND)

    def _point(self, pos: tuple[float, float]) -> tuple[int, int]:
        return (
            round(self.offset[0] + pos[0] * self.scale),
            round(self.offset[1] + pos[1] * self.scale),
        )

    def _rect(self, rect: pygame.Rect) -> pygame.Rect:
        return pygame.Rect(
            round(self.offset[0] + rect.x * self.scale),
            round(self.offset[1] + rect.y * self.scale),
            max(1, round(rect.width * self.scale)),
            max(1, round(rect.height * self.scale)),
        )

    def _radius(self, radius: float) -> int:
        return max(1, round(radius * self.scale))

    def _width(self, width: float) -> int:
        return max(1, round(width * self.scale))

    def _blit(self, source: pygame.Surface, pos: tuple[float, float]) -> None:
        self.surface.blit(source, self._point(pos))

    def _blit_center(self, source: pygame.Surface, center: tuple[float, float]) -> None:
        self.surface.blit(source, source.get_rect(center=self._point(center)))

    def draw_setup(
        self,
        panel: pygame.Rect,
        steppers: list[Stepper],
        buttons: list[Button],
        option_rows: list[tuple[str, str]],
        error: str | None,
        mouse_pos: tuple[int, int] | None = None,
    ) -> None:
        self.clear()
        title = self.title_font.render("Graph Theft Auto", True, colors.TEXT)
        self._blit_center(title, (panel.centerx, panel.top - 48))

        scaled_panel = self._rect(panel)
        pygame.draw.rect(self.surface, colors.PANEL_BG, scaled_panel, border_radius=self._radius(8))
        pygame.draw.rect(
            self.surface,
            colors.PANEL_BORDER,
            scaled_panel,
            width=self._width(1),
            border_radius=self._radius(8),
        )

        x = panel.x + 35
        y = panel.y + 30
        for stepper in steppers:
            stepper.draw(self.surface, self.font, x, y, mouse_pos, self.scale, self.offset)
            y += 54

        option_y = panel.y + 258
        for label, value in option_rows:
            label_surface = self.font.render(label, True, colors.TEXT)
            self._blit(label_surface, (x, option_y + 5))
            value_rect = pygame.Rect(panel.x + 206, option_y, 205, 30)
            scaled_value_rect = self._rect(value_rect)
            pygame.draw.rect(self.surface, colors.VERTEX, scaled_value_rect, border_radius=self._radius(4))
            pygame.draw.rect(
                self.surface,
                colors.PANEL_BORDER,
                scaled_value_rect,
                width=self._width(1),
                border_radius=self._radius(4),
            )
            value_surface = self.small_font.render(value, True, colors.TEXT)
            self.surface.blit(value_surface, value_surface.get_rect(center=scaled_value_rect.center))
            option_y += 48

        for button in buttons:
            button.draw(self.surface, self.font, mouse_pos, self.scale, self.offset)

        if error:
            err = self.small_font.render(error, True, colors.ERROR)
            self._blit(err, (x, panel.bottom - 23))

    def draw_game(
        self,
        state: GameState,
        layout: GraphLayout,
        rules: GameRules,
        board_rect: pygame.Rect,
        panel_rect: pygame.Rect,
        buttons: list[Button],
        legal_vertices: set[int] | None = None,
        move_prompt: str | None = None,
        staged_cop_destinations: tuple[int, ...] = (),
        mode_label: str = "Player vs Player",
        bot_label: str = "-",
        mouse_pos: tuple[int, int] | None = None,
    ) -> None:
        self.clear()
        title = self.title_font.render("Graph Theft Auto", True, colors.TEXT)
        self._blit(title, (20, 18))

        scaled_board = self._rect(board_rect)
        scaled_panel = self._rect(panel_rect)
        pygame.draw.rect(self.surface, (250, 250, 250), scaled_board, border_radius=self._radius(8))
        pygame.draw.rect(
            self.surface,
            colors.PANEL_BORDER,
            scaled_board,
            width=self._width(1),
            border_radius=self._radius(8),
        )
        pygame.draw.rect(self.surface, colors.PANEL_BG, scaled_panel, border_radius=self._radius(8))
        pygame.draw.rect(
            self.surface,
            colors.PANEL_BORDER,
            scaled_panel,
            width=self._width(1),
            border_radius=self._radius(8),
        )

        if legal_vertices is None:
            legal_vertices = {move for move in rules.get_legal_moves(state) if isinstance(move, int)}
        self._draw_graph(state, layout, legal_vertices, staged_cop_destinations)
        self._draw_panel(
            state,
            panel_rect,
            buttons,
            move_prompt,
            staged_cop_destinations,
            mode_label,
            bot_label,
            mouse_pos,
        )

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
        mode_label: str,
        bot_label: str,
        mouse_pos: tuple[int, int] | None = None,
    ) -> None:
        self.clear()
        title = self.title_font.render("Graph Theft Auto", True, colors.TEXT)
        self._blit(title, (20, 18))

        scaled_board = self._rect(board_rect)
        scaled_panel = self._rect(panel_rect)
        pygame.draw.rect(self.surface, (250, 250, 250), scaled_board, border_radius=self._radius(8))
        pygame.draw.rect(
            self.surface,
            colors.PANEL_BORDER,
            scaled_board,
            width=self._width(1),
            border_radius=self._radius(8),
        )
        pygame.draw.rect(self.surface, colors.PANEL_BG, scaled_panel, border_radius=self._radius(8))
        pygame.draw.rect(
            self.surface,
            colors.PANEL_BORDER,
            scaled_panel,
            width=self._width(1),
            border_radius=self._radius(8),
        )

        selectable = set(graph.vertices())
        selectable.difference_update(selected_cop_positions)
        self._draw_placement_graph(graph, layout, selectable, selected_cop_positions)
        self._draw_placement_panel(
            graph,
            panel_rect,
            buttons,
            round_limit,
            selected_cop_positions,
            cop_count,
            mode_label,
            bot_label,
            mouse_pos,
        )

    def _draw_graph(
        self,
        state: GameState,
        layout: GraphLayout,
        legal_moves: set[int],
        staged_cop_destinations: tuple[int, ...] = (),
    ) -> None:
        positions = layout.positions
        for u, v in state.graph.edges():
            pygame.draw.line(
                self.surface,
                colors.EDGE,
                self._point(positions[u]),
                self._point(positions[v]),
                width=self._width(2),
            )

        for vertex, pos in positions.items():
            if vertex in legal_moves:
                pygame.draw.circle(
                    self.surface,
                    colors.LEGAL_MOVE,
                    self._point(pos),
                    self._radius(self.VERTEX_RADIUS + 7),
                )
                pygame.draw.circle(
                    self.surface,
                    colors.LEGAL_MOVE_OUTLINE,
                    self._point(pos),
                    self._radius(self.VERTEX_RADIUS + 7),
                    width=self._width(2),
                )
            pygame.draw.circle(self.surface, colors.VERTEX, self._point(pos), self._radius(self.VERTEX_RADIUS))
            pygame.draw.circle(
                self.surface,
                colors.VERTEX_OUTLINE,
                self._point(pos),
                self._radius(self.VERTEX_RADIUS),
                width=self._width(2),
            )
            label = self.small_font.render(str(vertex), True, colors.TEXT)
            self._blit_center(label, pos)

        self._draw_tokens(state, positions, staged_cop_destinations)

    def _draw_tokens(
        self,
        state: GameState,
        positions: dict[int, tuple[float, float]],
        staged_cop_destinations: tuple[int, ...] = (),
    ) -> None:
        robber_pos = positions[state.robber_position]
        for index, cop_position in enumerate(state.cop_positions, start=1):
            display_position = staged_cop_destinations[index - 1] if index <= len(staged_cop_destinations) else cop_position
            cop_pos = positions[display_position]
            token_center = (cop_pos[0] - 12, cop_pos[1] - 18)
            if index <= len(staged_cop_destinations):
                pygame.draw.circle(
                    self.surface,
                    colors.LEGAL_MOVE_OUTLINE,
                    self._point(token_center),
                    self._radius(14),
                )
            self._draw_cop_car(token_center, index=index, scale=0.78)
        self._draw_robber_marker((robber_pos[0] + 14, robber_pos[1] - 18), scale=0.92)

    def _draw_placement_graph(
        self,
        graph: GraphModel,
        layout: GraphLayout,
        selectable: set[int],
        selected_cop_positions: tuple[int, ...],
    ) -> None:
        positions = layout.positions
        for u, v in graph.edges():
            pygame.draw.line(
                self.surface,
                colors.EDGE,
                self._point(positions[u]),
                self._point(positions[v]),
                width=self._width(2),
            )

        for vertex, pos in positions.items():
            if vertex in selectable:
                pygame.draw.circle(
                    self.surface,
                    colors.LEGAL_MOVE,
                    self._point(pos),
                    self._radius(self.VERTEX_RADIUS + 7),
                )
                pygame.draw.circle(
                    self.surface,
                    colors.LEGAL_MOVE_OUTLINE,
                    self._point(pos),
                    self._radius(self.VERTEX_RADIUS + 7),
                    width=self._width(2),
                )
            pygame.draw.circle(self.surface, colors.VERTEX, self._point(pos), self._radius(self.VERTEX_RADIUS))
            pygame.draw.circle(
                self.surface,
                colors.VERTEX_OUTLINE,
                self._point(pos),
                self._radius(self.VERTEX_RADIUS),
                width=self._width(2),
            )
            label = self.small_font.render(str(vertex), True, colors.TEXT)
            self._blit_center(label, pos)

        for index, selected_cop_position in enumerate(selected_cop_positions, start=1):
            cop_pos = positions[selected_cop_position]
            token_center = (cop_pos[0] - 12, cop_pos[1] - 18)
            self._draw_cop_car(token_center, index=index, scale=0.78)

    def _draw_cop_car(self, center: tuple[float, float], index: int, scale: float = 1.0) -> None:
        x, y = self._point(center)
        scale *= self.scale
        body = pygame.Rect(0, 0, int(34 * scale), int(18 * scale))
        body.center = (round(x), round(y))
        roof = pygame.Rect(0, 0, int(17 * scale), int(10 * scale))
        roof.center = (round(x), round(y - 7 * scale))
        wheel_radius = max(2, round(3 * scale))

        pygame.draw.rect(self.surface, (245, 248, 255), body, border_radius=round(4 * scale))
        pygame.draw.rect(
            self.surface,
            colors.COP,
            body,
            width=max(1, round(2 * scale)),
            border_radius=round(4 * scale),
        )
        pygame.draw.rect(self.surface, (180, 220, 255), roof, border_radius=round(3 * scale))
        pygame.draw.rect(self.surface, colors.VERTEX_OUTLINE, body, width=1, border_radius=round(4 * scale))
        pygame.draw.circle(self.surface, colors.VERTEX_OUTLINE, (body.left + round(8 * scale), body.bottom), wheel_radius)
        pygame.draw.circle(self.surface, colors.VERTEX_OUTLINE, (body.right - round(8 * scale), body.bottom), wheel_radius)
        pygame.draw.circle(self.surface, (230, 50, 50), (round(x - 4 * scale), roof.top), max(2, round(2 * scale)))
        pygame.draw.circle(self.surface, colors.COP, (round(x + 4 * scale), roof.top), max(2, round(2 * scale)))

        badge_radius = max(5, round(7 * scale))
        badge_center = (body.right - badge_radius + 1, body.top + badge_radius - 1)
        pygame.draw.circle(self.surface, colors.COP, badge_center, badge_radius)
        pygame.draw.circle(self.surface, (255, 255, 255), badge_center, badge_radius, width=1)
        label = self.small_font.render(str(index), True, (255, 255, 255))
        self.surface.blit(label, label.get_rect(center=badge_center))

    def _draw_robber_marker(self, center: tuple[float, float], scale: float = 1.0) -> None:
        x, y = center
        self._draw_stolen_car((x + 8 * scale, y + 10 * scale), scale * 0.72)
        self._draw_black_clad_robber((x - 8 * scale, y - 2 * scale), scale)

    def _draw_stolen_car(self, center: tuple[float, float], scale: float = 1.0) -> None:
        x, y = self._point(center)
        scale *= self.scale
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
        x, y = self._point(center)
        scale *= self.scale
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
        for start, end in [
            ((round(x - 7 * scale), arm_y), (round(x - 15 * scale), round(y + 11 * scale))),
            ((round(x + 7 * scale), arm_y), (round(x + 13 * scale), round(y + 9 * scale))),
            ((round(x - 3 * scale), leg_top), (round(x - 9 * scale), round(y + 24 * scale))),
            ((round(x + 3 * scale), leg_top), (round(x + 9 * scale), round(y + 24 * scale))),
        ]:
            pygame.draw.line(self.surface, outline, start, end, width=max(2, round(4 * scale)))

        pygame.draw.circle(self.surface, black, head_center, head_radius)
        pygame.draw.rect(self.surface, dark, torso, border_radius=round(4 * scale))
        for start, end in [
            ((round(x - 7 * scale), arm_y), (round(x - 15 * scale), round(y + 11 * scale))),
            ((round(x + 7 * scale), arm_y), (round(x + 13 * scale), round(y + 9 * scale))),
            ((round(x - 3 * scale), leg_top), (round(x - 9 * scale), round(y + 24 * scale))),
            ((round(x + 3 * scale), leg_top), (round(x + 9 * scale), round(y + 24 * scale))),
        ]:
            pygame.draw.line(self.surface, black, start, end, width=max(1, round(2.5 * scale)))

        eye_y = head_center[1] - round(1 * scale)
        eye_band = pygame.Rect(round(x - 6 * scale), eye_y - 2, max(7, round(12 * scale)), max(3, round(4 * scale)))
        pygame.draw.rect(self.surface, gray, eye_band, border_radius=round(2 * scale))
        pygame.draw.circle(self.surface, (245, 245, 245), (head_center[0] - round(2 * scale), eye_y), max(1, round(1.2 * scale)))
        pygame.draw.circle(self.surface, (245, 245, 245), (head_center[0] + round(2 * scale), eye_y), max(1, round(1.2 * scale)))

    def _draw_panel(
        self,
        state: GameState,
        panel_rect: pygame.Rect,
        buttons: list[Button],
        move_prompt: str | None,
        staged_cop_destinations: tuple[int, ...],
        mode_label: str,
        bot_label: str,
        mouse_pos: tuple[int, int] | None,
    ) -> None:
        x = panel_rect.x + 22
        y = panel_rect.y + 22
        heading = self.heading_font.render("Status", True, colors.TEXT)
        self._blit(heading, (x, y))
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
        if move_prompt is not None:
            lines.append(move_prompt)
        if staged_cop_destinations:
            staged_label = ", ".join(str(vertex) for vertex in staged_cop_destinations)
            lines.append(f"planned: {staged_label}")
        lines.append(f"mode: {mode_label}")
        lines.append(f"bot: {bot_label}")
        if state.status is GameStatus.COP_WIN:
            status_color = colors.COP
        elif state.status is GameStatus.ROBBER_WIN:
            status_color = colors.ROBBER
        else:
            status_color = colors.TEXT

        for line in lines:
            color = status_color if line.startswith("status:") else colors.TEXT
            text = self.font.render(line, True, color)
            self._blit(text, (x, y))
            y += 29

        y = self._hint_y(y + 12, buttons)
        hint_lines = ["Click highlighted vertices.", "R: restart   N: new graph"]
        for line in hint_lines:
            text = self.small_font.render(line, True, colors.MUTED_TEXT)
            self._blit(text, (x, y))
            y += 22

        for button in buttons:
            button.draw(self.surface, self.font, mouse_pos, self.scale, self.offset)

    def _draw_placement_panel(
        self,
        graph: GraphModel,
        panel_rect: pygame.Rect,
        buttons: list[Button],
        round_limit: int,
        selected_cop_positions: tuple[int, ...],
        cop_count: int,
        mode_label: str,
        bot_label: str,
        mouse_pos: tuple[int, int] | None,
    ) -> None:
        x = panel_rect.x + 22
        y = panel_rect.y + 22
        heading = self.heading_font.render("Start Positions", True, colors.TEXT)
        self._blit(heading, (x, y))
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
            f"mode: {mode_label}",
            f"bot: {bot_label}",
            prompt,
            f"cop starts: {selected_label}",
            "robber: -",
        ]
        for line in lines:
            color = colors.COP if line.startswith("Cop ") else colors.TEXT
            if line.startswith("Robber:"):
                color = colors.ROBBER
            text = self.font.render(line, True, color)
            self._blit(text, (x, y))
            y += 29

        y = self._hint_y(y + 12, buttons)
        hint_lines = ["Click highlighted vertices.", "Cop and robber must differ."]
        for line in hint_lines:
            text = self.small_font.render(line, True, colors.MUTED_TEXT)
            self._blit(text, (x, y))
            y += 22

        for button in buttons:
            button.draw(self.surface, self.font, mouse_pos, self.scale, self.offset)

    def _hint_y(self, preferred_y: int, buttons: list[Button]) -> int:
        if not buttons:
            return preferred_y
        first_button_y = min(button.rect.y for button in buttons)
        return min(preferred_y, first_button_y - 58)
