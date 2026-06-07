"""Small Pygame widgets used by the setup and side panel."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from cops_and_robbers.ui import colors


def _scaled_point(pos: tuple[float, float], scale: float, offset: tuple[int, int]) -> tuple[int, int]:
    return (round(offset[0] + pos[0] * scale), round(offset[1] + pos[1] * scale))


def _scaled_rect(rect: pygame.Rect, scale: float, offset: tuple[int, int]) -> pygame.Rect:
    return pygame.Rect(
        round(offset[0] + rect.x * scale),
        round(offset[1] + rect.y * scale),
        max(1, round(rect.width * scale)),
        max(1, round(rect.height * scale)),
    )


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    action: str
    enabled: bool = True

    def contains(self, pos: tuple[int, int]) -> bool:
        return self.enabled and self.rect.collidepoint(pos)

    def draw(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        mouse_pos: tuple[int, int] | None = None,
        scale: float = 1.0,
        offset: tuple[int, int] = (0, 0),
    ) -> None:
        if mouse_pos is None:
            mouse_pos = pygame.mouse.get_pos()
        bg = colors.BUTTON_HOVER if self.contains(mouse_pos) else colors.BUTTON_BG
        border = colors.BUTTON_BORDER if self.enabled else colors.PANEL_BORDER
        text_color = colors.TEXT if self.enabled else colors.MUTED_TEXT
        rect = _scaled_rect(self.rect, scale, offset)
        radius = max(1, round(6 * scale))
        pygame.draw.rect(surface, bg, rect, border_radius=radius)
        pygame.draw.rect(surface, border, rect, width=max(1, round(scale)), border_radius=radius)
        label = font.render(self.label, True, text_color)
        surface.blit(label, label.get_rect(center=rect.center))


@dataclass
class Stepper:
    label: str
    value: int
    minus_action: str
    plus_action: str
    min_value: int
    max_value: int

    def make_buttons(self, x: int, y: int) -> tuple[Button, Button]:
        minus_enabled = self.value > self.min_value
        plus_enabled = self.value < self.max_value
        return (
            Button(pygame.Rect(x + 132, y, 34, 30), "-", self.minus_action, minus_enabled),
            Button(pygame.Rect(x + 218, y, 34, 30), "+", self.plus_action, plus_enabled),
        )

    def draw(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        x: int,
        y: int,
        mouse_pos: tuple[int, int] | None = None,
        scale: float = 1.0,
        offset: tuple[int, int] = (0, 0),
    ) -> None:
        label_surface = font.render(self.label, True, colors.TEXT)
        surface.blit(label_surface, _scaled_point((x, y + 5), scale, offset))

        value_rect = pygame.Rect(x + 170, y, 44, 30)
        scaled_value_rect = _scaled_rect(value_rect, scale, offset)
        radius = max(1, round(4 * scale))
        pygame.draw.rect(surface, colors.VERTEX, scaled_value_rect, border_radius=radius)
        pygame.draw.rect(
            surface,
            colors.PANEL_BORDER,
            scaled_value_rect,
            width=max(1, round(scale)),
            border_radius=radius,
        )
        value_surface = font.render(str(self.value), True, colors.TEXT)
        surface.blit(value_surface, value_surface.get_rect(center=scaled_value_rect.center))

        for button in self.make_buttons(x, y):
            button.draw(surface, font, mouse_pos, scale, offset)
