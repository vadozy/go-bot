from __future__ import annotations
import enum
from typing import NamedTuple


class Player(enum.Enum):
    black = 1
    white = 2

    @property
    def opposite(self) -> Player:
        return Player.black if self == Player.white else Player.white


class Point(NamedTuple):
    row: int
    col: int

    def __deepcopy__(self) -> Point:
        return self
