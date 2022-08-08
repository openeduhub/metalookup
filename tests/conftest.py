import contextlib
import json
import logging
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Optional
from unittest import mock
from unittest.mock import Mock

import pytest
from playwright.async_api import Request, Response

from metalookup.core.content import Content


@contextlib.contextmanager
def lighthouse_mock(score: float = 0.98, status=200, detail: Optional[str] = None):
    """
    Mock the request to the lighthouse service of the accessibility extractor. This allows running unittests without
    a dependency on a running lighthouse container.
    Use the status and detail kwargs to simulate a failed request.
    """

    async def client_mock(self, url, **kwargs):  # noqa
        async def json():
            if status == 200:
                return {"score": [score]}
            else:
                return {"detail": detail}

        return Mock(status=status, json=json)

    with mock.patch("aiohttp.ClientSession.post", client_mock):
        yield


@contextlib.contextmanager
def playwright_mock(key: str = None):
    """
    Mock the communication with playwright by replacing the _fetch call of the Content class.
    This allows running unittests without a dependency on a running playwright container.

    This function loads the data from a HAR file from the test resources and directly assigns
    to the private variables of the Content class.
    """

    async def fetch(self: Content):
        with open(Path(__file__).parent / "resources" / "har" / f"{key}.json", "r") as f:
            splash = json.load(f)

        def convert_headers(headers) -> dict[str, str]:
            return {h["name"]: h["value"] for h in headers}

        def convert_entry(entry) -> tuple[Request, Response]:
            request = Mock(
                # add other fields here on demand.
                url=entry["request"]["url"],
                method=entry["response"]["status"],
                headers=convert_headers(entry["request"]["headers"]),
            )
            return (
                request,
                Mock(
                    status=entry["response"]["status"],
                    text=Mock(side_effect=splash["html"]),
                    headers=convert_headers(entry["response"]["headers"]),
                    request=request,
                ),
            )

        entries = splash["har"]["log"]["entries"]
        self._html = splash["html"]
        if len(entries) > 0:
            self._headers = convert_headers(entries[-1]["response"]["headers"])
            # need to convert to string values!
            self._cookies = [{k: str(v) for k, v in c.dict()} for c in entries[-1]["response"]["cookies"]]
            _, self._response = convert_entry(entries[-1])
            self._requests = [convert_entry(entry)[0] for entry in entries]
            self._responses = [convert_entry(entry)[1] for entry in entries]

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
