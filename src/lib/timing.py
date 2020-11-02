from datetime import datetime


def get_utc_now():
    return datetime.utcnow().timestamp()
