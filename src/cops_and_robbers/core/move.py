"""Move history records."""

from dataclasses import dataclass

from cops_and_robbers.core.player import PlayerRole


@dataclass(frozen=True)
class Move:
    player: PlayerRole
    destinations: tuple[int, ...]

    @classmethod
    def cop(cls, destinations: tuple[int, ...] | list[int]) -> "Move":
        return cls(PlayerRole.COP, tuple(destinations))

    @classmethod
    def robber(cls, destination: int) -> "Move":
        return cls(PlayerRole.ROBBER, (destination,))


@dataclass(frozen=True)
class MoveRecord:
    player: PlayerRole
    from_vertices: tuple[int, ...]
    to_vertices: tuple[int, ...]
    round_number: int

    @property
    def from_vertex(self) -> int:
        return self.from_vertices[0]

    @property
    def to_vertex(self) -> int:
        return self.to_vertices[0]
