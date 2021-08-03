import time
from datetime import datetime

global_start = time.perf_counter()


def get_utc_now() -> float:
    return datetime.utcnow().timestamp()
