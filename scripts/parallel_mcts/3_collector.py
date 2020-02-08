import zmq
import sys
from time import time
from typing import List

from dlgo.gotypes import Player


def main():
    # Client sends tasks to this port synchronously
    context = zmq.Context()
    collector_server = context.socket(zmq.REP)
    collector_server.bind("tcp://*:5559")

    # Socket to receive solutions on
    receiver = context.socket(zmq.PULL)
    receiver.bind("tcp://*:5558")

    j = 0
    batch = 0
    white_wins, black_wins = 0, 0
    print("[Collector Server] started...")
    sys.stdout.flush()
    start = time()  # seconds
    while True:
        solutions: List[Player] = []
        # Received signal about the start of batch
        tasks_count = int(collector_server.recv_string())
        # print("Collector received signal that {} tasks' solutions are coming soon...")

        # Collect tasks solutions
        for i in range(tasks_count):
            s = receiver.recv_pyobj()
            # print("Received solution number {}".format(i + 1))
            solutions.append(s)

        collector_server.send_pyobj(solutions)
        j += tasks_count
        for winner in solutions:
            if winner == Player.white:
                white_wins += 1
            else:
                black_wins += 1
        if j >= 1000:
            end = time()  # seconds
            delta = end - start
            batch += 1
            print("250x4 batch {}: white_wins [ {} ], black_wins [ {} ] [{:>5.1f} sec]".format(batch,
                                                                                               white_wins,
                                                                                               black_wins,
                                                                                               delta))
            sys.stdout.flush()
            start = time()  # seconds
            j = 0
            white_wins, black_wins = 0, 0
            if batch == 60:
                batch = 0


if __name__ == '__main__':
    main()
