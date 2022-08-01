import contextlib
import json
import logging
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Optional
from unittest import mock
from unittest.mock import Mock

import pytest

from metalookup.app.splash_models import SplashResponse

# @contextlib.contextmanager
# def lighthouse_mock(score: float = 0.98):
#     """
#     Mock the request to the lighthouse service of the accessibility extractor. This allows running unittests without
#     a dependency on a running lighthouse container.
#     """
#
#     async def accessibility_api_call_mock(self, url, session, strategy) -> float:  # noqa
#         return score
#
#     with mock.patch("metalookup.features.accessibility.Accessibility._execute_api_call", accessibility_api_call_mock):
#         yield


@contextlib.contextmanager
def lighthouse_mock(score: float = 0.98, status=200, detail: Optional[str] = None):
    """
    Mock the request to the lighthouse service of the accessibility extractor. This allows running unittests without
    a dependency on a running lighthouse container.
    Use the status and detail kwargs to simulate a failed request.
    """

    async def client_mock(self, url, **kwargs):  # noqa
        from aiohttp import ClientResponse

        async def json():
            if status == 200:
                return {"score": [score]}
            else:
                return {"detail": detail}

        return Mock(status=status, json=json)

    # intercept the request to the non-running splash and lighthouse container
    # and instead use the checked in response json and a hardcoded score value
    with mock.patch("aiohttp.ClientSession.get", client_mock):
        yield


@contextlib.contextmanager
def splash_mock(key: str = None):
    """
    Mock the request to splash in case of a missing splash response field of the incoming extract requests by loading
    the data from the test resources. This allows running unittests without a dependency on a running splash container.
    """

    async def fetch(self) -> SplashResponse:
        with open(Path(__file__).parent / "resources" / "splash" / f"{key}.json", "r") as f:
            response = SplashResponse.parse_obj(json.load(f))
            # Would need to be self.url == response.requestedURL, because splash
            # uses the redirect url as the URL. I.e. if we ask splash for 'https://google.com' splash will put
            # 'https://www.google.com/' into the url.
            # assert self.url == response.url, "Loaded resource URL does not match content URL"
            return response

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
