import random
import numpy as np
from typing import List, Tuple, Iterator


class MSE:

    def __init__(self):
        pass

    @staticmethod
    def loss_function(predictions: np.ndarray, labels: np.ndarray) -> float:
        diff = predictions - labels
        return 0.5 * sum(diff * diff)

    # Gradient vector
    @staticmethod
    def loss_derivative(predictions: np.ndarray, labels: np.ndarray) -> np.ndarray:
        return predictions - labels
