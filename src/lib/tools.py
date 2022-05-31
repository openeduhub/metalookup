import math
import os
from distutils import util


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
