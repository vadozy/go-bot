import random

from .base import Agent
from .helpers import is_point_an_eye
from dlgo.goboard import GameState, Move
from typing import List
from dlgo.minimax.alphabeta import alphabeta


class AlphaBetaAgent(Agent):

    def __init__(self, max_depth: int, ev_fn):
        Agent.__init__(self)
        self.max_depth = max_depth
        self.ev_fn = ev_fn

    def select_move(self, game_state: GameState):
        best_moves: List[Move] = []
        best_score = float("-inf")
        # Loop over all legal moves.
        for possible_move in game_state.legal_moves():
            if possible_move.point and is_point_an_eye(game_state.board, possible_move.point, game_state.next_player):
                continue  # skip the eye
            next_state = game_state.apply_move(possible_move)
            result = alphabeta(next_state, False, game_state.next_player, self.max_depth, ev_fn=self.ev_fn)
            if (not best_moves) or result > best_score:
                best_moves = [possible_move]
                best_score = result
            elif result == best_score:
                best_moves.append(possible_move)
        # For variety, randomly select among all equally good moves.
        return random.choice(best_moves)
