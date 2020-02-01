from dlgo.goboard import Board
from dlgo.gotypes import Player, Point
from typing import List

CHAR_TO_PLAYER = {
    '.': None,
    'x': Player.black,
    'o': Player.white,
}

# 9x9 is OK
board_empty: List[str] = [
    '.........',
    '.........',
    '.........',
    '.........',
    '.........',
    '.........',
    '.........',
    '.........',
    '.........',
]


def board_from_list(board_list: List[str]) -> Board:
    board: Board = Board(len(board_list), len(board_list[0]))
    for row, line in enumerate(board_list, 1):
        for col, ch in enumerate(line, 1):
            if ch != '.':
                board.place_stone(CHAR_TO_PLAYER[ch], Point(row, col))
    return board


def test_empty_board():
    expected: Board = Board(len(board_empty), len(board_empty[0]))
    actual: Board = board_from_list(board_empty)
    assert expected == actual


def test_is_self_capture_01():
    b: List[str] = [
        '.x.......',  # Point(1, 1)
        'xx.......',
        '.........',
        '..o...x..',
        '.o.o.o.o.',  # Point(5, 3) and Point(5, 7)
        '..o...o..',
        '........o',
        'xo.....ox',
        '.xo...ox.',  # Point(9, 1) and Point(9, 9)
    ]
    board = board_from_list(b)

    assert board.is_self_capture(Player.white, Point(1, 1))
    assert not board.is_self_capture(Player.black, Point(1, 1))

    assert board.is_self_capture(Player.black, Point(5, 3))
    assert not board.is_self_capture(Player.white, Point(5, 3))

    assert not board.is_self_capture(Player.black, Point(5, 7))
    assert not board.is_self_capture(Player.white, Point(5, 7))

    assert not board.is_self_capture(Player.white, Point(9, 1))
    assert not board.is_self_capture(Player.black, Point(9, 1))

    assert board.will_capture(Player.white, Point(9, 9))
    assert not board.is_self_capture(Player.white, Point(9, 9))
    assert board.is_self_capture(Player.black, Point(9, 9))
