from datetime import datetime


def get_utc_now() -> float:
    return datetime.utcnow().timestamp()
