from dlgo.goboard import GameState, GoString
from dlgo.gotypes import Player, Point
from typing import Set


def eval_fn(game_state: GameState, original_player: Player) -> int:
    score = 0
    for r in range(1, game_state.board.num_rows + 1):
        for c in range(1, game_state.board.num_cols + 1):
            p = Point(r, c)
            color = game_state.board.get(p)
            if color == original_player:
                score += 1
            elif color == original_player.opposite:
                score -= 1
    return score


def eval_fn2(game_state: GameState, original_player: Player) -> float:
    score = 0.0
    my_go_strings: Set[GoString] = set()
    his_go_strings: Set[GoString] = set()
    for r in range(1, game_state.board.num_rows + 1):
        for c in range(1, game_state.board.num_cols + 1):
            p = Point(r, c)
            go_string = game_state.board.get_go_string(p)
            if go_string:
                if go_string.color == original_player:
                    my_go_strings.add(go_string)
                else:
                    his_go_strings.add(go_string)
    for gs in my_go_strings:
        score += len(gs.stones) ** 1.8 + len(gs.liberties)
    for gs in his_go_strings:
        score -= len(gs.stones) ** 1.8 + len(gs.liberties)
    return score


def alphabeta(game_state: GameState, maximizing: bool, original_player: Player, max_depth: int = 2,
              alpha: float = float("-inf"), beta: float = float("inf"), ev_fn=None) -> float:
    if game_state.is_over():
        if game_state.winner() == original_player:
            return float("inf")
        else:
            return float("-inf")

    if max_depth == 0:
        return ev_fn(game_state, original_player)

    # Recursive case - maximize your gains or minimize the opponent's gains
    if maximizing:
        for move in game_state.legal_moves():
            result = alphabeta(game_state.apply_move(move), False, original_player, max_depth - 1, alpha, beta, ev_fn)
            alpha = max(result, alpha)
            if beta <= alpha:
                break
        return alpha
    else:  # minimizing
        for move in game_state.legal_moves():
            result = alphabeta(game_state.apply_move(move), True, original_player, max_depth - 1, alpha, beta, ev_fn)
            beta = min(result, beta)
            if beta <= alpha:
                break
        return beta
