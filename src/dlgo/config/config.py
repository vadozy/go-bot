import os
import configparser

config = configparser.ConfigParser()
config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'dlgo.cfg'))

# USAGE
# from dlgo.config.config import config
# PARALLEL_ROLLOUTS = bool(int(config['ENGINE']['MCTS_PARALLEL']))
