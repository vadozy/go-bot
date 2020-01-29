from dlgo.agent.random_bot import RandomAgent
from dlgo.agent.base import Agent
from dlgo.goboard import GameState, Move
from dlgo import gotypes
from dlgo.scoring import compute_game_result
from dlgo.utils.utils import print_board, print_move, point_from_coords


def main():
    board_size = 9
    game: GameState = GameState.new_game(board_size)
    bot: Agent = RandomAgent()

    move: Move = None
    while not game.is_over():
        print('\033c')  # clear terminal [Linux and OS X]
        if move is not None:
            print_move(game.next_player, move)
        print_board(game.board)
        if game.next_player == gotypes.Player.black:
            print(compute_game_result(game))
            human_move_str: str = input('-- ')
            try:
                point = point_from_coords(human_move_str.strip().upper())
                move = Move.play(point)
            except (ValueError, Exception):
                move = Move.pass_turn()
        else:
            move = bot.select_move(game)
        game = game.apply_move(move)


if __name__ == '__main__':
    main()
