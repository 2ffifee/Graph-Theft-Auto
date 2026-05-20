"""Move history records."""

from dataclasses import dataclass

from cops_and_robbers.core.player import PlayerRole


@dataclass(frozen=True)
class MoveRecord:
    player: PlayerRole
    from_vertex: int
    to_vertex: int
    round_number: int
