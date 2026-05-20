"""Small Pygame widgets used by the setup and side panel."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from cops_and_robbers.ui import colors


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    action: str
    enabled: bool = True

    def contains(self, pos: tuple[int, int]) -> bool:
        return self.enabled and self.rect.collidepoint(pos)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        mouse_pos = pygame.mouse.get_pos()
        bg = colors.BUTTON_HOVER if self.contains(mouse_pos) else colors.BUTTON_BG
        border = colors.BUTTON_BORDER if self.enabled else colors.PANEL_BORDER
        text_color = colors.TEXT if self.enabled else colors.MUTED_TEXT
        pygame.draw.rect(surface, bg, self.rect, border_radius=6)
        pygame.draw.rect(surface, border, self.rect, width=1, border_radius=6)
        label = font.render(self.label, True, text_color)
        surface.blit(label, label.get_rect(center=self.rect.center))


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

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, x: int, y: int) -> None:
        label_surface = font.render(self.label, True, colors.TEXT)
        surface.blit(label_surface, (x, y + 5))

        value_rect = pygame.Rect(x + 170, y, 44, 30)
        pygame.draw.rect(surface, colors.VERTEX, value_rect, border_radius=4)
        pygame.draw.rect(surface, colors.PANEL_BORDER, value_rect, width=1, border_radius=4)
        value_surface = font.render(str(self.value), True, colors.TEXT)
        surface.blit(value_surface, value_surface.get_rect(center=value_rect.center))

        for button in self.make_buttons(x, y):
            button.draw(surface, font)
