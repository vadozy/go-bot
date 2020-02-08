import os
from multiprocessing import Process, Lock
import time
import signal
import subprocess
import io


def now():
    return time.ctime(time.time())


RUN = True


def on_signal(signum, stackframe):
    global RUN
    print('Got signal', signum, 'at', now())
    RUN = False


def launch_process(process_name, lock):
    absolute_path = os.path.dirname(os.path.realpath(__file__)) + "/" + process_name
    proc = subprocess.Popen(["python", absolute_path], stdout=subprocess.PIPE)
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        print(line, end="")


if __name__ == '__main__':
    # install signal handler for keyboard interrupt
    signal.signal(signal.SIGINT, on_signal)
    lock = Lock()

    p = Process(target=launch_process, args=('1_server.py', lock))
    p.start()

    p = Process(target=launch_process, args=('2_worker.py', lock))
    p.start()
    p = Process(target=launch_process, args=('2_worker.py', lock))
    p.start()
    p = Process(target=launch_process, args=('2_worker.py', lock))
    p.start()
    p = Process(target=launch_process, args=('2_worker.py', lock))
    p.start()

    p = Process(target=launch_process, args=('3_collector.py', lock))
    p.start()

    with lock:
        print('To stop use keyboard interrupt...')
    while RUN:
        signal.pause()
