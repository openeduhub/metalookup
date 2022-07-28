import contextlib
import json
import logging
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from unittest import mock
from unittest.mock import AsyncMock

import pytest

from metalookup.app.splash_models import HAR, SplashResponse


@contextlib.contextmanager
def lighthouse_mock(score: float = 0.98):
    """
    Mock the request to the lighthouse service of the accessibility extractor. This allows running unittests without
    a dependency on a running lighthouse container.
    """

    async def accessibility_api_call_mock(self, url, session, strategy) -> float:  # noqa
        return score

    with mock.patch("metalookup.features.accessibility.Accessibility._execute_api_call", accessibility_api_call_mock):
        yield


@contextlib.contextmanager
def splash_mock():
    """
    Mock the request to splash in case of a missing splash response field of the incoming extract requests by loading
    the data from the test resources. This allows running unittests without a dependency on a running splash container.
    """

    async def fetch(self) -> tuple[str, HAR]:
        url = self.url
        if url.startswith("https://www.google.com"):
            path = Path(__file__).parent / "resources" / "splash-response-google.json"
        elif url.startswith("https://wirlernenonline.de/does-not-exist.html"):
            path = Path(__file__).parent / "resources" / "splash-response-404.json"
        else:
            raise ValueError(f"Cannot provide mocked splash response for {url=}")
        with open(path, "r") as f:
            response = SplashResponse.parse_obj(json.load(f))
            return response.html, response.har

    with mock.patch("metalookup.core.content.Content._fetch", new=fetch):
        yield


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
