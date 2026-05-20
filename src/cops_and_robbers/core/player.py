"""Player role definitions."""

from enum import Enum


class PlayerRole(Enum):
    COP = "cop"
    ROBBER = "robber"

    @property
    def label(self) -> str:
        return "Cop" if self is PlayerRole.COP else "Robber"
