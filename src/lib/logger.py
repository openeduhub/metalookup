import logging
import os
import time
from logging import handlers

from lib.constants import LOGFILE_MANAGER
from lib.settings import LOG_LEVEL, LOG_PATH


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGFILE_MANAGER)


def create_logger() -> logging.Logger:
    logger = get_logger()

    logger.propagate = False

    logger.setLevel(LOG_LEVEL)

    formatter = logging.Formatter("%(asctime)s  %(levelname)-7s %(message)s")

    # Convert time to UTC/GMT time
    logging.Formatter.converter = time.gmtime

    # standard log
    dir_path = os.path.dirname(os.path.realpath(__file__))

    data_path = dir_path + "/" + LOG_PATH

    log_15_mb_limit = 1024 * 1024 * 15
    backup_count = 10000

    if not os.path.exists(data_path):
        os.mkdir(data_path, mode=0o755)

    fh = handlers.RotatingFileHandler(
        filename=f"{data_path}/{LOGFILE_MANAGER}.log",
        maxBytes=log_15_mb_limit,
        backupCount=backup_count,
    )

    fh.setLevel(LOG_LEVEL)
    fh.setFormatter(formatter)

    # error log
    error_handler = handlers.RotatingFileHandler(
        filename=f"{data_path}/{LOGFILE_MANAGER}_error.log",
        maxBytes=log_15_mb_limit,
        backupCount=backup_count,
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(error_handler)
    return logger
