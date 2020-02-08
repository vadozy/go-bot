from __future__ import annotations
import zmq
import sys

from dlgo.mcts.mcts import MCTSAgent
from dlgo.goboard import GameState
from dlgo.gotypes import Player


def main():
    context = zmq.Context()
    # Socket to receive messages on
    receiver = context.socket(zmq.PULL)
    receiver.connect("tcp://localhost:5557")

    # Sockets to send solutions to
    collector = context.socket(zmq.PUSH)
    collector.connect("tcp://localhost:5558")

    print("[Worker] started...")
    sys.stdout.flush()
    # Process tasks forever
    while True:
        task: GameState = receiver.recv_pyobj()
        # print("Received task")

        # Do the work
        winner: Player = MCTSAgent.simulate_random_game(task)

        # Send results to collector
        collector.send_pyobj(winner)


if __name__ == '__main__':
    main()
