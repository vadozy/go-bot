from typing import NamedTuple, Tuple, Set, List, Optional, Dict, Union
from dlgo.gotypes import Player, Point
from dlgo.goboard_slow import Board, GameState


class Territory:
    def __init__(self, territory_map):
        self.num_black_territory = 0
        self.num_white_territory = 0
        self.num_black_stones = 0
        self.num_white_stones = 0
        self.num_dame = 0
        self.dame_points = []
        for point, status in territory_map.items():
            if status == Player.black:
                self.num_black_stones += 1
            elif status == Player.white:
                self.num_white_stones += 1
            elif status == 'territory_b':
                self.num_black_territory += 1
            elif status == 'territory_w':
                self.num_white_territory += 1
            elif status == 'dame':
                self.num_dame += 1
                self.dame_points.append(point)


class GameResult(NamedTuple):
    b: int
    w: int
    komi: float

    @property
    def winner(self):
        if self.b > self.w + self.komi:
            return Player.black
        return Player.white

    @property
    def winning_margin(self):
        w = self.w + self.komi
        return abs(self.b - w)

    def __str__(self):
        w = self.w + self.komi
        if self.b > w:
            return 'B+%.1f' % (self.b - w,)
        return 'W+%.1f' % (w - self.b,)


def evaluate_territory(board: Board) -> Territory:
    """
    Map a board into territory and dame.

    Any points that are completely surrounded by a single color are
    counted as territory; it makes no attempt to identify even
    trivially dead groups.
    """
    status: Dict[Point, Union[Player, str]] = {}
    for r in range(1, board.num_rows + 1):
        for c in range(1, board.num_cols + 1):
            p = Point(row=r, col=c)
            if p in status:
                continue
            stone = board.get(p)
            if stone is not None:
                status[p] = stone
            else:
                group, neighbors = _collect_region(p, board)
                if len(neighbors) == 1:
                    neighbor_stone = neighbors.pop()
                    stone_str = 'b' if neighbor_stone == Player.black else 'w'
                    fill_with = 'territory_' + stone_str
                else:
                    fill_with = 'dame'

                for pos in group:
                    status[pos] = fill_with
    return Territory(status)


def _collect_region(start_pos: Point, board: Board, visited: Set[Point] = None) -> \
        Tuple[List[Point], Set[Optional[Player]]]:
    """
    Find the contiguous section of a board containing a point. Also
    identify all the boundary points.

    start_pos can be empty or it can have a player (black or white)
    Returns List of contiguous points (empty points, usually) and set of bordering Players

    For example, if start_pos is empty, the bordering player set can be {White}, {Black} or {White, Black}.
        But also, if start_pos has White Player, the bordering player set can be {None}, {Black} or {None, Black}
    """
    if visited is None:
        visited = set()
    if start_pos in visited:
        return [], set()
    all_points = [start_pos]
    all_borders: Set[Optional[Player]] = set()
    visited.add(start_pos)
    player_at_start_pos: Optional[Player] = board.get(start_pos)
    next_points = board.neighbors(start_pos)
    for next_p in next_points:
        player_neighbor: Optional[Player] = board.get(next_p)
        if player_neighbor == player_at_start_pos:
            points, borders = _collect_region(next_p, board, visited)
            all_points += points
            all_borders |= borders
        else:
            all_borders.add(player_neighbor)
    return all_points, all_borders


def compute_game_result(game_state: GameState):
    territory = evaluate_territory(game_state.board)
    return GameResult(
            territory.num_black_territory + territory.num_black_stones,
            territory.num_white_territory + territory.num_white_stones,
            komi=7.5)
