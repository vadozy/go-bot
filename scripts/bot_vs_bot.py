from dlgo.goboard import GameState
import dlgo.gotypes as gotypes
from dlgo.scoring import compute_game_result
from dlgo.agent.random_bot import RandomBot
from dlgo.utils.utils import print_board, print_move
import time

from dlgo.utils.profiling import result_str


def main():
    board_size = 9
    game: GameState = GameState.new_game(board_size)
    bots = {
        gotypes.Player.black: RandomBot(),
        gotypes.Player.white: RandomBot(),
    }
    while not game.is_over():
        time.sleep(0.3)

        print('\033c')  # clear terminal [Linux and OS X]
        print_board(game.board)
        bot_move = bots[game.next_player].select_move(game)
        print_move(game.next_player, bot_move)
        game = game.apply_move(bot_move)
        print(compute_game_result(game))

    print(compute_game_result(game))
    print(result_str())


if __name__ == '__main__':
    main()
