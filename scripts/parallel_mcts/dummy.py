import time
import os
import sys

counter = 0
if __name__ == "__main__":
    while True:
        counter += 1
        print("dummy: {}".format(counter))
        print(os.path.dirname(os.path.realpath(__file__)))
        sys.stdout.flush()
        time.sleep(5)
