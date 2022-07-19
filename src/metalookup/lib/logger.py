import logging
import os
import time
from logging import handlers
from pathlib import Path
from typing import Optional


def setup_logging(level: str, path: Optional[Path] = None):
    """
    :param level: The log level to be used.
    :param path: The path where to put log files. If None, then logs will only be printed to standard output.
    """
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    root = logging.getLogger()
    root.setLevel(level)

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")

    # Convert time to UTC/GMT time
    logging.Formatter.converter = time.gmtime

    log_15_mb_limit = 1024 * 1024 * 15
    backup_count = 10000

    if path is not None:
        if not os.path.exists(path):
            os.mkdir(path, mode=0o755)

        fh = handlers.RotatingFileHandler(
            filename=f"{path}/meta-lookup.log",
            maxBytes=log_15_mb_limit,
            backupCount=backup_count,
        )

        fh.setLevel(level)
        fh.setFormatter(formatter)

        # error log
        error_handler = handlers.RotatingFileHandler(
            filename=f"{path}/meta-lookup-error.log",
            maxBytes=log_15_mb_limit,
            backupCount=backup_count,
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)

        root.addHandler(fh)
        root.addHandler(error_handler)

    # debug messages from the pdfminer cause significant performance overhead.
    disabled_loggers = {"pdfminer"}
    for name in disabled_loggers:
        root = logging.getLogger(name)
        root.setLevel("WARN")
