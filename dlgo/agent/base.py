from abc import ABC, abstractmethod
from dlgo.goboard_slow import GameState, Move

__all__ = [
    'Agent',
]


class Agent(ABC):
    def __init__(self):
        ...

    @abstractmethod
    def select_move(self, game_state: GameState) -> Move:
        ...

    @staticmethod
    def diagnostics():
        return {}
