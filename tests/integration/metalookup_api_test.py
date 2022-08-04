import json
import os
import pprint
from pathlib import Path

import pytest
from httpx import AsyncClient

from metalookup.app.api import Input, app, cache_backend, manager
from metalookup.app.models import LRMISuggestions, MetadataTags, Output
from metalookup.features.licence import DetectedLicences
from tests.conftest import lighthouse_mock, playwright_mock


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

    if cache_backend is not None:
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
    """
    This test:
     - mocks lighthouse and playwright
     - tests the whole application flow through the API layer
     - uses whatever caching is configured in the client fixture
    """

    with playwright_mock(key="google.com"), lighthouse_mock():
        input = Input(url="https://www.google.com/")
        response = await client.post("/extract", json=input.dict(), timeout=10, headers={"Cache-Control": "no-cache"})

    pprint.pprint(response.json())

    assert response.status_code == 200

    # make sure, that our result actually complies with the promised open api spec.
    output = Output.parse_obj(json.loads(response.text))
    assert output.url == input.url
    assert isinstance(output.security, MetadataTags), "did not receive data for security extractor"
    assert isinstance(output.accessibility, MetadataTags), "did not receive data for accessibility extractor"


@pytest.mark.asyncio
async def test_suggest_endpoint(client):
    """
    This test:
     - mocks lighthouse and playwright
     - tests the whole application flow through the API layer
     - uses whatever caching is configured in the client fixture
    """
    with playwright_mock(key="google.com"), lighthouse_mock():
        input = Input(url="https://www.google.com/")
        response = await client.post(
            "/suggestions", json=input.dict(), timeout=10, headers={"Cache-Control": "no-cache"}
        )
    assert response.status_code == 200
    response = json.loads(response.text)

    assert "ccm:oeh_quality_protection_of_minors" in response
    assert "ccm:oeh_quality_login" in response
    assert "ccm:oeh_quality_data_privacy" in response
    assert "ccm:accessibilitySummary" in response

    # make sure, that our result actually complies with the promised open api spec.
    suggestion = LRMISuggestions.parse_obj(response)
    assert isinstance(suggestion.accessibility, MetadataTags)


@pytest.mark.asyncio
async def test_extract_endpoint_cache(client):
    """
    This test:
     - does not require the playwright container because it mocks the service dependency with static data
     - does not need the lighthouse container because it
         - either expects the lighthouse extractor to fail (with a timeout or connection refused)
         - or mocks the function where the request to lighthouse is issued
         - or loads the response from cache (no need to issue a request)
     - does not need postgres container because it uses sqlite cache backend
    """

    with playwright_mock(key="google.com"), lighthouse_mock():
        response = await client.post(
            "/extract",
            json=Input(url="https://www.google.com/").dict(),
            timeout=10,
            headers={"Cache-Control": "only-if-cached"},
        )
        assert response.status_code == 404, "response can be cached but is not present in cache."

        response = await client.post(
            "/extract",
            json=Input(url="https://www.google.com/").dict(),
            timeout=10,
            headers={"Cache-Control": "max-age=5000"},
        )
        assert response.status_code == 200

        output = Output.parse_obj(json.loads(response.text))
        assert output.url == "https://www.google.com/"
        assert isinstance(output.security, MetadataTags), "did not receive data for security extractor"

        assert (
            await cache_backend.get(key="https://www.google.com/") is None
        ), "should not be cached, as it was not a complete result"

        with lighthouse_mock():
            # now we should get a fully populated result (now Errors within the individual extractors)
            # which should also get cached.
            response = await client.post(
                "/extract?extra=true",
                json=Input(url="https://www.google.com/").dict(),
                timeout=10,
            )

            # make sure, that our result actually complies with the promised open api spec.
            output = Output.parse_obj(json.loads(response.text))

            pprint.pprint(output.dict())

            assert response.status_code == 200, response.text
            assert (
                cache_backend.get(key="https://www.google.com/") is not None
            ), "should be cached, as it was a complete result"

            assert output.url == "https://www.google.com/"
            assert isinstance(output.licence.extra, dict)
            # should be possible to deserialize the extra data
            print(DetectedLicences.parse_obj(output.licence.extra))
            assert isinstance(output.security, MetadataTags), "did not receive data for security extractor"
            # This should not be present, as the request to the accessibility container will fail
            assert isinstance(
                output.accessibility, MetadataTags
            ), "received accessibility result but container should not be running"
