from functools import wraps
from time import time
from typing import Dict, List
from statistics import mean, median, stdev

"""
This module is used for tuning and profiling
"""

_FORMAT_STR_HEADER = "{:<30}  | {:>10}{:>10}{:>15}{:>10}{:>10}{:>10}{:>10}{:>10}"
# _FORMAT_STR_VALUES = "{:<30} -> {:>10.1E}{:>10.1%}{:>15}{:>10.2E}{:>10.2E}{:>10.2E}{:>10.2E}{:>10.2E}"
_FORMAT_STR_VALUES = "{:<30} -> {:>10.1f}{:>10.1%}{:>15}{:>10.2f}{:>10.2f}{:>10.2f}{:>10.2f}{:>10.2f}"


_MODULE_LOAD_TIME = time()  # seconds


def _total_program_execution_time() -> float:
    """
    In seconds
    """
    return time() - _MODULE_LOAD_TIME


class FunctionProfilingData:
    def __init__(self, f_name):
        self.f_name: str = f_name  # function name
        self.f_execution_times: List[float] = []  # all function execution times (milliseconds)

    def record_execution_time(self, t: float) -> None:
        self.f_execution_times.append(t)

    @property
    def f_calls(self) -> int:
        """
        Number of calls to this function
        """
        return len(self.f_execution_times)

    @property
    def f_mean(self) -> float:
        """
        Average (or mean) function execution time (milliseconds)
        """
        return mean(self.f_execution_times)

    @property
    def f_total(self) -> float:
        """
        Total function execution time (SECONDS)
        """
        return sum(self.f_execution_times) / 1000

    @property
    def f_median(self) -> float:
        """
        Median function execution time (milliseconds)
        """
        return median(self.f_execution_times)

    @property
    def f_max(self) -> float:
        """
        Maximum function execution time (milliseconds)
        """
        return max(self.f_execution_times)

    @property
    def f_min(self) -> float:
        """
        Minimum function execution time (milliseconds)
        """
        return min(self.f_execution_times)

    @property
    def f_stdev(self) -> float:
        """
        Standard Deviation of function execution time (milliseconds)
        """
        return stdev(self.f_execution_times)

    @property
    def f_pct(self) -> float:
        """
        Percentage of this function execution time (with respect to the whole program exec time)
        """
        return self.f_total / _total_program_execution_time()

    def __str__(self) -> str:
        return _FORMAT_STR_VALUES.format(self.f_name, self.f_total, self.f_pct, self.f_calls, self.f_min, self.f_mean,
                                         self.f_median, self.f_max, self.f_stdev)


_result: Dict[str, FunctionProfilingData] = {}


def timing(f):
    """
    Decorator to measure time of a function
    Usage:

    from dlgo.utils.profiling import timing, result, result_str

    @timing
    def f(a):
        for _ in range(a):
            pass

    print(result_str)
    # "result()" returns the Dict that has all the data, if needed

    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time() * 1000  # turn seconds to milliseconds
        function_return_value = f(*args, **kwargs)
        end = time() * 1000  # turn seconds to milliseconds

        f_name = f.__name__
        profiling_data: FunctionProfilingData = _result.setdefault(f_name, FunctionProfilingData(f_name))
        profiling_data.record_execution_time(end - start)

        return function_return_value

    return wrapper


def result() -> Dict[str, FunctionProfilingData]:
    return _result.copy()


def result_str() -> str:
    ret = "### " * 30 + "\n"
    ret += "FUNCTION EXECUTION TIME REPORT\n"
    ret += "CLEAN Program Time (s): {:>10.1f}\n".format(_total_program_execution_time())
    ret += "*** " * 30 + "\n"
    ret += _FORMAT_STR_HEADER.format("Function Name", "TOTAL", "Percent", "Calls", "Min", "Mean", "Median", "Max", "Stdev")
    ret += "\n" + _FORMAT_STR_HEADER.format("", "sec", "", "times", "ms", "ms", "ms", "ms", "ms")
    ret += "\n" + _FORMAT_STR_HEADER.format("-" * 30, "----", "----", "----", "----", "----", "----", "----", "----")
    for v in _result.values():
        ret += "\n" + str(v)
    ret += "\n" + "*** " * 30
    ret += "\nTotal Program Time (s): {:>10.1f}".format(_total_program_execution_time())
    ret += "\n" + "*** " * 30
    return ret
