from __future__ import annotations
from dlgo.utils.profiling import timing, result, FunctionProfilingData
import time


@timing
def meaning_of_life_function(sleep_time) -> int:
    time.sleep(sleep_time)
    return 42


def test_empty_result():
    assert len(result()) == 0


def test_dummy_result():
    sleep_time = 0.05  # seconds
    ret = meaning_of_life_function(sleep_time)
    assert ret == 42
    assert len(result()) == 1
    data: FunctionProfilingData = result()["meaning_of_life_function"]
    assert data.f_calls == 1
    assert sleep_time - sleep_time / 4 < data.f_mean / 1000 < sleep_time + sleep_time / 4
