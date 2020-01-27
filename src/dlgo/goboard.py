from __future__ import annotations
from .scoring import compute_game_result
import copy
from dlgo.gotypes import Player, Point
from typing import Iterable, Dict, Optional, List, Tuple, cast, Set, FrozenSet
from dlgo import zobrist

from dlgo.utils.profiling import timing


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
    def play(cls, point) -> Move:
        return Move(point=point)

    @classmethod
    def pass_turn(cls) -> Move:
        return Move(is_pass=True)

    @classmethod
    def resign(cls) -> Move:
        return Move(is_resign=True)


class GoString:
    """
    Immutable !
    Keeps track of a group of connected stones and their liberties
    """

    def __init__(self, color: Player, stones: Iterable[Point], liberties: Iterable[Point]):
        self.color = color
        self.stones = frozenset(stones)
        self.liberties = frozenset(liberties)

    def without_liberty(self, point: Point):
        new_liberties = self.liberties - {point}
        return GoString(self.color, self.stones, new_liberties)

    def with_liberty(self, point: Point):
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

    def __eq__(self, other) -> bool:
        return isinstance(other, GoString) \
               and self.color == other.color \
               and self.stones == other.stones
        # and self.liberties == other.liberties
        # Last line is not needed. If color and stones are the same, liberties must be the same too.

    def __hash__(self) -> int:
        return hash(self.color) ^ hash(self.stones) ^ hash(self.liberties)

    def __deepcopy__(self, memodict=None):
        return self


class Board:
    def __init__(self, num_rows: int, num_cols: int):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self._grid: Dict[Point, Optional[GoString]] = {}
        self._hash = zobrist.EMPTY_BOARD

    @timing
    def place_stone(self, player: Player, point: Point):
        assert self.is_on_grid(point)
        assert self._grid.get(point) is None
        adjacent_same_color: List[GoString] = []
        adjacent_opposite_color: List[GoString] = []
        liberties: List[Point] = []
        for neighbor in self.neighbors(point):
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
                self._replace_string_in_grid(replacement)
            else:
                self._remove_string(other_color_string)

    def _replace_string_in_grid(self, new_string: GoString):
        for point in new_string.stones:
            self._grid[point] = new_string

    def _remove_string(self, string: GoString):
        for point in string.stones:
            for neighbor in self.neighbors(point):
                neighbor_string = self._grid.get(neighbor)
                if neighbor_string is None:
                    continue
                if neighbor_string is not string:
                    self._replace_string_in_grid(neighbor_string.with_liberty(point))
            self._grid[point] = None
            self._hash ^= zobrist.HASH_CODE[point, string.color]

    def is_on_grid(self, point: Point) -> bool:
        return 1 <= point.row <= self.num_rows and 1 <= point.col <= self.num_cols

    def neighbors(self, point: Point) -> List[Point]:
        return self.points_at_delta(point, [(0, 1), (0, -1), (-1, 0), (1, 0)])

    def points_at_delta(self, point: Point, deltas: Iterable[Tuple[int, int]]) -> List[Point]:
        # assert self.is_on_grid(point)
        ret = []
        for delta_r, delta_c in deltas:
            new_row = point.row + delta_r
            new_col = point.col + delta_c
            if 1 <= new_row <= self.num_rows and 1 <= new_col <= self.num_cols:
                ret.append(Point(new_row, new_col))
        return ret

    def get(self, point: Point) -> Optional[Player]:
        string = self._grid.get(point)
        if string is None:
            return None
        return string.color

    def get_go_string(self, point) -> Optional[GoString]:
        return self._grid.get(point)

    def __eq__(self, other) -> bool:
        return isinstance(other, Board) and \
               self.num_rows == other.num_rows and \
               self.num_cols == other.num_cols and \
               self._grid == other._grid

    def __deepcopy__(self, memodict=None):
        copied = Board(self.num_rows, self.num_cols)
        # Can do a shallow copy b/c the dictionary maps tuples
        # (immutable) to GoStrings (also immutable)
        copied._grid = copy.copy(self._grid)
        copied._hash = self._hash
        return copied

    def zobrist_hash(self):
        return self._hash


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
            self.previous_states = frozenset(previous_state.previous_states | {
                (previous_state.next_player, previous_state.board.zobrist_hash())
            })

    def apply_move(self, move: Move) -> GameState:
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

    @timing
    def is_move_self_capture(self, player: Player, move: Move) -> bool:
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, cast(Point, move.point))
        new_string = cast(GoString, next_board.get_go_string(move.point))
        return new_string.num_liberties == 0

    @property
    def situation(self) -> Tuple[Player, Board]:
        return self.next_player, self.board

    @timing
    def does_move_violate_ko(self, player: Player, move: Move) -> bool:
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        next_situation = (player.opposite, next_board.zobrist_hash())
        return next_situation in self.previous_states

    @timing
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
        moves = []
        for row in range(1, self.board.num_rows + 1):
            for col in range(1, self.board.num_cols + 1):
                move = Move.play(Point(row, col))
                if self.is_valid_move(move):
                    moves.append(move)
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
