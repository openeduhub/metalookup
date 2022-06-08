import json
import logging
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from unittest import mock

import pytest

from app.splash_models import SplashResponse
from core.website_manager import WebsiteData


def pytest_configure(config):
    """Disable noisy upstream loggers."""
    # From https://stackoverflow.com/a/57002853/2160256
    disabled_loggers = {"pdfminer"}
    for name in disabled_loggers:
        logger = logging.getLogger(name)
        logger.setLevel("WARN")  #


@pytest.fixture(scope="session")
def executor():
    # use as generator to make sure pool is clearly terminated after tests
    with ProcessPoolExecutor(max_workers=4) as pool:
        yield pool
