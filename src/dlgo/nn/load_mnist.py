import os
import gzip
import pickle
import numpy as np
from typing import List, Tuple, Iterator


def encode_label(j: int) -> np.ndarray:
    e = np.zeros(10)
    e[j] = 1.0
    return e


def shape_data(data: Tuple[np.ndarray, np.ndarray]) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
    features = (np.reshape(x, (784,)) for x in data[0])
    labels = (encode_label(y) for y in data[1])
    return zip(features, labels)


def load_data() -> Tuple[Iterator[Tuple[np.ndarray, np.ndarray]], Iterator[Tuple[np.ndarray, np.ndarray]]]:
    file_name = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'mnist.pkl.gz')
    with gzip.open(file_name, 'rb') as f:
        train_data, validation_data, test_data = pickle.load(f, encoding='bytes')
    return shape_data(train_data), shape_data(test_data)
