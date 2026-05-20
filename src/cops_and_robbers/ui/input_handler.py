"""Input helpers for Pygame events."""

from __future__ import annotations

import pygame

from cops_and_robbers.ui.graph_layout import GraphLayout
from cops_and_robbers.ui.renderer import Renderer
from cops_and_robbers.ui.widgets import Button


class InputHandler:
    def clicked_button(self, pos: tuple[int, int], buttons: list[Button]) -> str | None:
        for button in buttons:
            if button.contains(pos):
                return button.action
        return None

    def clicked_vertex(
        self,
        pos: tuple[int, int],
        board_rect: pygame.Rect,
        layout: GraphLayout | None,
    ) -> int | None:
        if layout is None or not board_rect.collidepoint(pos):
            return None
        return layout.get_vertex_at_position(pos[0], pos[1], Renderer.VERTEX_RADIUS + 8)
