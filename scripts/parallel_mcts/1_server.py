import zmq
import sys

_NUMBER_OF_PARALLEL_RUNS = 4


def main():
    context = zmq.Context()

    # Client sends tasks to this port synchronously
    sim_games_server = context.socket(zmq.REP)
    sim_games_server.bind("tcp://*:5555")

    # Socket to send each task to a worker node asynchronously
    # There are multiple worker nodes
    sender_to_workers = context.socket(zmq.PUSH)
    sender_to_workers.bind("tcp://*:5557")

    # Socket to talk to collector_server
    print("[Rollout Server]: connecting to [Collector Server] where solutions will be coming from...")
    collector_server = context.socket(zmq.REQ)
    collector_server.connect("tcp://localhost:5559")

    print("[Rollout Server] started...")
    sys.stdout.flush()
    while True:
        # Wait for next set of tasks from client
        task = sim_games_server.recv_pyobj()

        tasks_count = _NUMBER_OF_PARALLEL_RUNS
        # print("Received task".format(task))

        # The first message is the count of tasks and signals start of batch
        collector_server.send_string("{}".format(tasks_count))

        for i in range(tasks_count):
            # print("Sending to worker a task")
            sender_to_workers.send_pyobj(task)

        solutions = collector_server.recv_pyobj()
        # print("Received {} solutions, sending back...".format(len(solutions)))
        sim_games_server.send_pyobj(solutions)


if __name__ == '__main__':
    main()
