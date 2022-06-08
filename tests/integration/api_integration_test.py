import json
import os
import pprint
from pathlib import Path
from unittest import mock
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.api import Input, app, cache_backend, manager
from app.models import Error, MetadataTags, Output
from app.splash_models import SplashResponse
from features.licence import DetectedLicences


@pytest.fixture()
async def client() -> AsyncClient:
    # clear cache before each test. We cannot use sqlite inmemory cache, because
    # the databases package creates a new inmemory sqlite connection for each request
    # essentially rendering the inmemory sqlite backend useless for caching.
    # See  https://github.com/encode/databases/issues/488
    cache_db = Path(__file__).parent.parent / "meta-lookup-cache.db"
    if os.path.exists(cache_db):
        os.remove(cache_db)
    from databases import Database

    cache_backend.database = Database("sqlite://./meta-lookup-cache.db")

    # Using an async client allows to have async unit tests which simplifies checking the desired
    # side effects (e.g. cache modifications). However it means we manually need to ensure that
    # the application state is setup.
    await cache_backend.setup()
    await manager.setup()

    async with AsyncClient(app=app, base_url="http://localhost") as client:
        yield client


@pytest.mark.asyncio
async def test_ping_endpoint(client):
    response = await client.get("/_ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_extract_endpoint(client):
    path = Path(__file__).parent.parent / "resources" / "splash-response-google.json"
    with open(path, "r") as f:
        splash = SplashResponse.parse_obj(json.load(f))

    input = Input(url="https://google.com", splash_response=splash)
    response = await client.post("/extract", json=input.dict(), timeout=10, headers={"Cache-Control": "no-cache"})

    pprint.pprint(response.json())

    assert response.status_code == 200

    # make sure, that our result actually complies with the promised open api spec.
    output = Output.parse_obj(json.loads(response.text))
    assert output.url == input.url
    assert isinstance(output.security, MetadataTags), "did not receive data for security extractor"
    # This should not be present, as the request to the accessibility container will fail
    assert isinstance(output.accessibility, Error), "received accessibility result but container should not be running"


@pytest.mark.asyncio
async def test_extract_endpoint_cache(client):
    path = Path(__file__).parent.parent / "resources" / "splash-response-google.json"
    with open(path, "r") as f:
        splash = SplashResponse.parse_obj(json.load(f))

    response = await client.post(
        "/extract",
        json=Input(url="https://google.com", splash_response=splash).dict(),
        timeout=10,
        headers={"Cache-Control": "only-if-cached"},
    )
    assert response.status_code == 400, "response cannot be cached, as the whole har body is part of the request."

    with mock.patch("core.website_manager.WebsiteData.fetch_content", new=AsyncMock(side_effect=lambda _: splash)):
        response = await client.post(
            "/extract",
            json=Input(url="https://google.com").dict(),
            timeout=10,
            headers={"Cache-Control": "only-if-cached"},
        )
        assert response.status_code == 404, "response can be cached but is not present in cache."

        response = await client.post(
            "/extract",
            json=Input(url="https://google.com").dict(),
            timeout=10,
            headers={"Cache-Control": "max-age=5000"},
        )
        assert response.status_code == 200

        output = Output.parse_obj(json.loads(response.text))
        assert output.url == "https://google.com"
        assert isinstance(output.security, MetadataTags), "did not receive data for security extractor"
        assert isinstance(output.accessibility, Error), "did not receive an error for accessibility"

        assert (
            await cache_backend.get(key="https://google.com") is None
        ), "should not be cached, as it was not a complete result"

        with mock.patch(
            "features.accessibility.Accessibility._execute_api_call",
            new=AsyncMock(side_effect=lambda website_data, session, strategy: 0.1337),
        ):
            # now we should get a fully populated result (now Errors within the individual extractors)
            # which should also get cached.
            response = await client.post(
                "/extract",
                json=Input(url="https://google.com").dict(),
                timeout=10,
            )

            # make sure, that our result actually complies with the promised open api spec.
            output = Output.parse_obj(json.loads(response.text))

            pprint.pprint(output.dict())

            assert response.status_code == 200, response.text
            assert (
                cache_backend.get(key="https://google.com") is not None
            ), "should be cached, as it was a complete result"

            assert output.url == "https://google.com"
            assert isinstance(output.security, MetadataTags), "did not receive data for security extactor"
            # This should not be present, as the request to the accessibility container will fail
            assert isinstance(
                output.accessibility, MetadataTags
            ), "received accessibility result but container should not be running"
