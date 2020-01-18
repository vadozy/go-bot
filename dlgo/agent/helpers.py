from dlgo.gotypes import Point, Player
from dlgo.goboard_slow import Board
from typing import List

__all__ = [
    'is_point_an_eye',
]


def is_point_an_eye(board: Board, point: Point, color: Player):
    """
    For our purposes, an eye is an empty point where all adjacent points and at least three out of four diagonally
    adjacent points are filled with friendly stones.
    NOTE Experienced Go players may notice that the preceding definition of eye will miss a valid eye in some cases.
    We’ll accept those errors to keep the implementation simple.
    """
    if board.get(point) is not None:
        return False
    for neighbor in board.neighbors(point):
        neighbor_color = board.get(neighbor)
        if neighbor_color != color:
            return False

    friendly_corners: int = 0
    off_board_corners: int = 0
    corners: List[Point] = [
        Point(point.row - 1, point.col - 1),
        Point(point.row - 1, point.col + 1),
        Point(point.row + 1, point.col - 1),
        Point(point.row + 1, point.col + 1),
    ]
    for corner in corners:
        if board.is_on_grid(corner):
            corner_color = board.get(corner)
            if corner_color == color:
                friendly_corners += 1
        else:
            off_board_corners += 1
    if off_board_corners > 0:
        return off_board_corners + friendly_corners == 4
    return friendly_corners >= 3
