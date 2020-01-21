import random
from typing import Dict, Tuple

from dlgo.gotypes import Player, Point


def to_python(player_state: Player):
    if player_state is None:
        return 'None'
    if player_state == Player.black:
        return Player.black
    return Player.white


_64_BITS = 2 ** 64 - 1

table: Dict[Tuple[Point, Player], int] = {}
empty_board = 0
for row in range(1, 20):
    for col in range(1, 20):
        for state in (Player.black, Player.white):
            code = random.randint(0, _64_BITS)
            table[Point(row, col), state] = code

print('from .gotypes import Player, Point')
print('')
print('HASH_CODE = {')
for (pt, state), hash_code in table.items():
    print('    (%r, %s): %r,' % (pt, to_python(state), hash_code))
print('}')
print('')
print('EMPTY_BOARD = %d' % (empty_board,))
