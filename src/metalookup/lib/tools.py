import math
from contextlib import contextmanager
from time import perf_counter


@contextmanager
def runtime() -> float:
    """
    Context manager to measure execution time of a with block.

    Example usage:

    ```
    with runtime() as t:
        import time
        time.sleep(1)

    print(f"Execution time: {t():.4f} secs")
    ```
    """
    start = perf_counter()
    yield lambda: perf_counter() - start


def get_mean(values: list) -> float:
    return sum(values) / len(values)


def get_std_dev(values: list) -> float:
    mean = get_mean(values)
    var = sum(pow(x - mean, 2) for x in values) / len(values)  # variance
    std = math.sqrt(var)
    return std


def get_unique_list(items: list) -> list:
    seen = set()
    for element in range(len(items) - 1, -1, -1):
        item = items[element]
        if item in seen:
            del items[element]
        else:
            seen.add(item)
    return items
