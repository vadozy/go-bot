from dlgo.goboard import GameState
import dlgo.gotypes as gotypes
from dlgo.scoring import compute_game_result
from dlgo.mcts.mcts import MCTSAgent
from dlgo.utils.utils import print_board, print_move

from dlgo.utils.profiling import result_str


def main():
    board_size = 7
    game: GameState = GameState.new_game(board_size)
    bots = {
        # gotypes.Player.white: MCTSAgent(4000, temperature=1.4),
        gotypes.Player.white: MCTSAgent(5000, temperature=1.4, parallel_rollouts=True),
        gotypes.Player.black: MCTSAgent(5000, temperature=1.1, parallel_rollouts=True),
    }
    while not game.is_over():
        bot_move = bots[game.next_player].select_move(game)
        game = game.apply_move(bot_move)

        print('\033c')  # clear terminal [Linux and OS X]
        print_board(game.board)
        print_move(game.next_player.opposite, bot_move)
        print(compute_game_result(game))

    print(compute_game_result(game))


if __name__ == '__main__':
    main()
    print(result_str())
