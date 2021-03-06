from dlgo.goboard import GameState
import dlgo.gotypes as gotypes
from dlgo.scoring import compute_game_result
from dlgo.agent.random_bot import RandomAgent, FastRandomAgent
from dlgo.agent.alphabeta_bot import AlphaBetaAgent
from dlgo.mcts.mcts import MCTSAgent
from dlgo.utils.utils import print_board, print_move
from dlgo.minimax.alphabeta import eval_fn, eval_fn2
import time

from dlgo.utils.profiling import result_str


def main():
    board_size = 7
    game: GameState = GameState.new_game(board_size)
    bots = {
        # gotypes.Player.black: RandomBot(),
        # gotypes.Player.black: AlphaBetaAgent(max_depth=0, ev_fn=eval_fn2),
        # gotypes.Player.white: RandomAgent(),
        # gotypes.Player.black: RandomAgent(),
        # gotypes.Player.white: FastRandomAgent(),
        # gotypes.Player.black: FastRandomAgent(),
        # gotypes.Player.black: AlphaBetaAgent(max_depth=1, ev_fn=eval_fn),
        gotypes.Player.black: MCTSAgent(2500, temperature=1.4, parallel_rollouts=True),
        gotypes.Player.white: AlphaBetaAgent(max_depth=3, ev_fn=eval_fn2),
    }
    while not game.is_over():
        # time.sleep(0.5)
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
