import contextlib
import json
import os
import pprint
from pathlib import Path

import pytest
from httpx import AsyncClient

from lighthouse.api import Input, Output, app


@pytest.fixture()
async def client() -> AsyncClient:
    async with AsyncClient(app=app, base_url="http://localhost") as client:
        yield client


@pytest.mark.asyncio
async def test_ping_endpoint(client):
    response = await client.get("/_ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@contextlib.contextmanager
def popen_mock():
    """Mock the call to asyncio.create_subprocess_exec."""

    def popen(*args, **kwargs):
        class MockedProcess:
            def __init__(self, *args, **kwargs):
                self.returncode = 0

            async def communicate(self) -> tuple[bytes, bytes]:
                # return the minimal structure required from lighthouse standard output
                return b'{"categories":{"accessibility":{"score":0.1337}}}', b"stderr mock"

        return MockedProcess(*args, **kwargs)

    from unittest import mock
    from unittest.mock import AsyncMock

    with mock.patch("asyncio.create_subprocess_exec", new=AsyncMock(side_effect=popen)) as mocked:
        yield mocked


@pytest.mark.asyncio
async def test_accessibility_endpoint(client):
    """
    This test:
     - does not need lighthouse installed / configured, because it mocks the process.Open call.
    """
    input = Input(url="https://google.com", strategy="desktop")
    with popen_mock():
        response = await client.post("/accessibility", json=input.dict(), timeout=1)

    assert response.status_code == 200

    # make sure, that our result actually complies with the promised open api spec.
    Output.parse_obj(json.loads(response.text))
