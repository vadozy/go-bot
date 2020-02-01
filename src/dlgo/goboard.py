from __future__ import annotations
import copy
from dlgo.gotypes import Player, Point
from dlgo.scoring import compute_game_result
from dlgo import zobrist
from dlgo.utils.utils import MoveAge
from typing import Tuple, Dict, List, Iterable, Optional, FrozenSet, cast

from dlgo.utils.profiling import timing

__all__ = [
    'Board',
    'GameState',
    'Move',
    'GoString'
]

neighbor_tables = {}
corner_tables = {}


def init_neighbor_table(dim: Tuple[int, int]):
    rows, cols = dim
    new_table: Dict[Point, List[Point]] = {}
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            p = Point(row=r, col=c)
            full_neighbors = [
                Point(p.row - 1, p.col),
                Point(p.row + 1, p.col),
                Point(p.row, p.col - 1),
                Point(p.row, p.col + 1),
            ]
            true_neighbors = [
                n for n in full_neighbors
                if 1 <= n.row <= rows and 1 <= n.col <= cols]
            new_table[p] = true_neighbors
    neighbor_tables[dim] = new_table


def init_corner_table(dim: Tuple[int, int]):
    rows, cols = dim
    new_table: Dict[Point, List[Point]] = {}
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            p = Point(row=r, col=c)
            full_corners = [
                Point(p.row - 1, p.col - 1),
                Point(p.row - 1, p.col + 1),
                Point(p.row + 1, p.col - 1),
                Point(p.row + 1, p.col + 1),
            ]
            true_corners = [
                n for n in full_corners
                if 1 <= n.row <= rows and 1 <= n.col <= cols]
            new_table[p] = true_corners
    corner_tables[dim] = new_table


class IllegalMoveError(Exception):
    pass


class GoString:
    """
    Immutable !
    Keeps track of a group of connected stones and their liberties
    """

    def __init__(self, color: Player, stones: Iterable[Point], liberties: Iterable[Point]):
        self.color = color
        self.stones = frozenset(stones)
        self.liberties = frozenset(liberties)

    def without_liberty(self, point) -> GoString:
        new_liberties = self.liberties - {point}
        return GoString(self.color, self.stones, new_liberties)

    def with_liberty(self, point) -> GoString:
        new_liberties = self.liberties | {point}
        return GoString(self.color, self.stones, new_liberties)

    def merged_with(self, go_string: GoString) -> GoString:
        assert go_string.color == self.color
        combined_stones = self.stones | go_string.stones
        combined_liberties = (self.liberties | go_string.liberties) - combined_stones
        return GoString(self.color, combined_stones, combined_liberties)

    @property
    def num_liberties(self) -> int:
        return len(self.liberties)


class Board:
    def __init__(self, num_rows: int, num_cols: int):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self._grid: Dict[Point, Optional[GoString]] = {}
        self._hash = zobrist.EMPTY_BOARD

        dim = (num_rows, num_cols)
        if dim not in neighbor_tables:
            init_neighbor_table(dim)
        if dim not in corner_tables:
            init_corner_table(dim)
        self.neighbor_table = neighbor_tables[dim]
        self.corner_table = corner_tables[dim]
        self.move_ages = MoveAge(self)

    def neighbors(self, point) -> List[Point]:
        return self.neighbor_table[point]

    def corners(self, point) -> List[Point]:
        return self.corner_table[point]

    def place_stone(self, player: Player, point: Point):
        assert self.is_on_grid(point)
        if self._grid.get(point) is not None:
            print('Illegal play on %s' % str(point))
            raise IllegalMoveError()
        assert self._grid.get(point) is None
        adjacent_same_color: List[GoString] = []
        adjacent_opposite_color: List[GoString] = []
        liberties: List[Point] = []
        self.move_ages.increment_all()
        self.move_ages.add(point)
        for neighbor in self.neighbor_table[point]:
            neighbor_string = self._grid.get(neighbor)
            if neighbor_string is None:
                liberties.append(neighbor)
            elif neighbor_string.color == player:
                if neighbor_string not in adjacent_same_color:
                    adjacent_same_color.append(neighbor_string)
            else:
                if neighbor_string not in adjacent_opposite_color:
                    adjacent_opposite_color.append(neighbor_string)

        new_string = GoString(player, [point], liberties)

        for same_color_string in adjacent_same_color:
            new_string = new_string.merged_with(same_color_string)
        for new_string_point in new_string.stones:
            self._grid[new_string_point] = new_string

        self._hash ^= zobrist.HASH_CODE[point, player]

        for other_color_string in adjacent_opposite_color:
            replacement = other_color_string.without_liberty(point)
            if replacement.num_liberties:
                self._replace_string(replacement)
            else:
                self._remove_string(other_color_string)

    def _replace_string(self, new_string: GoString):
        for point in new_string.stones:
            self._grid[point] = new_string

    def _remove_string(self, string: GoString):
        for point in string.stones:
            self.move_ages.reset_age(point)
            # Removing a string can create liberties for other strings.
            for neighbor in self.neighbor_table[point]:
                neighbor_string = self._grid.get(neighbor)
                if neighbor_string is None:
                    continue
                if neighbor_string is not string:
                    self._replace_string(neighbor_string.with_liberty(point))
            self._grid[point] = None
            self._hash ^= zobrist.HASH_CODE[point, string.color]

    def is_self_capture(self, player: Player, point: Point) -> bool:
        friendly_strings = []
        for neighbor in self.neighbors(point):
            neighbor_string = self._grid.get(neighbor)
            if neighbor_string is None:
                # This point has a liberty. Can't be self capture.
                return False
            elif neighbor_string.color == player:
                # Gather for later analysis.
                friendly_strings.append(neighbor_string)
            else:
                if neighbor_string.num_liberties == 1:
                    # This move is real capture, not a self capture.
                    return False
        if all(neighbor.num_liberties == 1 for neighbor in friendly_strings):
            return True
        return False

    def will_capture(self, player: Player, point: Point) -> bool:
        for neighbor in self.neighbor_table[point]:
            neighbor_string = self._grid.get(neighbor)
            if neighbor_string is None:
                continue
            elif neighbor_string.color == player:
                continue
            else:
                if neighbor_string.num_liberties == 1:
                    # This move would capture.
                    return True
        return False

    def is_on_grid(self, point: Point) -> bool:
        return 1 <= point.row <= self.num_rows and 1 <= point.col <= self.num_cols

    def get(self, point: Point) -> Optional[Player]:
        string = self._grid.get(point)
        if string is None:
            return None
        return string.color

    def get_go_string(self, point: Point) -> Optional[GoString]:
        return self._grid.get(point)

    def __eq__(self, other):
        return isinstance(other, Board) and \
               self.num_rows == other.num_rows and \
               self.num_cols == other.num_cols and \
               self._hash == other._hash

    def __deepcopy__(self, memodict=None):
        copied = Board(self.num_rows, self.num_cols)
        # Can do a shallow copy b/c the dictionary maps tuples
        # (immutable) to GoStrings (also immutable)
        copied._grid = self._grid.copy()
        copied._hash = self._hash
        return copied

    def zobrist_hash(self) -> int:
        return self._hash


class Move:
    def __init__(self, point: Point = None, is_pass: bool = False, is_resign: bool = False):
        """
        Never call this constructor directly. Use @classmethod factories from this class.
        """
        self.point = point
        self.is_play = (self.point is not None)
        self.is_pass = is_pass
        self.is_resign = is_resign
        assert self.is_play + self.is_pass + self.is_resign == 1

    @classmethod
    def play(cls, point: Point) -> Move:
        """A move that places a stone on the board."""
        return Move(point=point)

    @classmethod
    def pass_turn(cls) -> Move:
        return Move(is_pass=True)

    @classmethod
    def resign(cls) -> Move:
        return Move(is_resign=True)

    def __str__(self):
        if self.is_pass:
            return 'pass'
        if self.is_resign:
            return 'resign'
        return '(r %d, c %d)' % (self.point.row, self.point.col)

    def __hash__(self):
        return hash((self.is_play, self.is_pass, self.is_resign, self.point))

    def __eq__(self, other):
        return (self.is_play, self.is_pass, self.is_resign, self.point) == \
               (other.is_play, other.is_pass, other.is_resign, other.point)


class GameState:
    def __init__(self, board: Board, next_player: Player, previous_state: Optional[GameState],
                 last_move: Optional[Move]):
        self.board = board
        self.next_player = next_player
        self.previous_state = previous_state
        self.last_move = last_move
        if previous_state is None:
            self.previous_states: FrozenSet[Tuple[Player, int]] = frozenset()
        else:
            self.previous_states = frozenset(
                previous_state.previous_states | {(previous_state.next_player, previous_state.board.zobrist_hash())})

    def apply_move(self, move: Move) -> GameState:
        """Return the new GameState after applying the move."""
        if move.is_play:
            point = cast(Point, move.point)
            next_board = copy.deepcopy(self.board)
            next_board.place_stone(self.next_player, point)
        else:
            next_board = self.board
        return GameState(next_board, self.next_player.opposite, self, move)

    @classmethod
    def new_game(cls, board_size: int) -> GameState:
        board = Board(board_size, board_size)
        return GameState(board, Player.black, None, None)

    def is_move_self_capture(self, player, move):
        if not move.is_play:
            return False
        return self.board.is_self_capture(player, move.point)

    @property
    def situation(self) -> Tuple[Player, Board]:
        return self.next_player, self.board

    def does_move_violate_ko(self, player: Player, move: Move) -> bool:
        if not move.is_play:
            return False
        point = cast(Point, move.point)
        if not self.board.will_capture(player, point):
            return False
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, point)
        next_situation = (player.opposite, next_board.zobrist_hash())
        return next_situation in self.previous_states

    def is_valid_move(self, move: Move) -> bool:
        if self.is_over():
            return False
        if move.is_pass or move.is_resign:
            return True
        return (
                self.board.get(cast(Point, move.point)) is None and
                not self.is_move_self_capture(self.next_player, move) and
                not self.does_move_violate_ko(self.next_player, move))

    def is_over(self) -> bool:
        if self.last_move is None:
            return False
        if self.last_move.is_resign:
            return True
        previous_state = cast(GameState, self.previous_state)
        second_last_move = previous_state.last_move
        if second_last_move is None:
            return False
        return self.last_move.is_pass and second_last_move.is_pass

    def legal_moves(self) -> List[Move]:
        if self.is_over():
            return []
        moves = []
        for row in range(1, self.board.num_rows + 1):
            for col in range(1, self.board.num_cols + 1):
                move = Move.play(Point(row, col))
                if self.is_valid_move(move):
                    moves.append(move)
        # These two moves are always legal.
        moves.append(Move.pass_turn())
        moves.append(Move.resign())

        return moves

    def winner(self) -> Optional[Player]:
        if not self.is_over():
            return None
        if self.last_move and self.last_move.is_resign:
            return self.next_player
        game_result = compute_game_result(self)
        return game_result.winner
