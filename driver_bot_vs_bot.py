from dlgo.goboard_slow import GameState
from dlgo.scoring import compute_game_result
from dlgo.agent.random_bot import RandomBot
from dlgo import gotypes
from dlgo.utils import print_board, print_move
import time


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


if __name__ == '__main__':
    main()
