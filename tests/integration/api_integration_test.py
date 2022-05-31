import json
import pprint
from pathlib import Path
from unittest import mock
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api import Input, app
from app.models import Error, MetadataTags, Output
from app.splash_models import SplashResponse


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as client:
        yield client


def test_ping_endpoint(client):
    response = client.get("/_ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_extract_endpoint(client):
    path = Path(__file__).parent.parent / "splash-response-google.json"
    with open(path, "r") as f:
        splash = SplashResponse.parse_obj(json.load(f))

    input = Input(url="https://google.com", splash_response=splash)
    response = client.post("/extract", data=input.json(), timeout=10, headers={"Cache-Control": "no-cache"})

    pprint.pprint(response.json())

    assert response.status_code == 200

    # make sure, that our result actually complies with the promised open api spec.
    output = Output.parse_obj(json.loads(response.text))
    assert output.url == input.url
    assert isinstance(output.security, MetadataTags), "did not receive data for security extactor"
    # This should not be present, as the request to the accessibility container will fail
    assert isinstance(output.accessibility, Error), "received accessibility result but container should not be running"


def test_extract_endpoint_cache(client):
    path = Path(__file__).parent.parent / "splash-response-google.json"
    with open(path, "r") as f:
        splash = SplashResponse.parse_obj(json.load(f))

    response = client.post(
        "/extract",
        data=Input(url="https://google.com", splash_response=splash).json(),
        timeout=10,
        headers={"Cache-Control": "only-if-cached"},
    )
    assert response.status_code == 400, "response cannot be cached, as the whole har body is part of the request."

    with mock.patch("core.website_manager.WebsiteData.fetch_content", new=AsyncMock(side_effect=lambda _: splash)):
        response = client.post(
            "/extract",
            data=Input(url="https://google.com").json(),
            timeout=10,
            headers={"Cache-Control": "only-if-cached"},
        )
        assert response.status_code == 404, "response can be cached but is not present in cache."

        response = client.post(
            "/extract",
            data=Input(url="https://google.com").json(),
            timeout=10,
            headers={"Cache-Control": "max-age=5000"},
        )
        assert response.status_code == 200

        output = Output.parse_obj(json.loads(response.text))
        assert output.url == "https://google.com"
        assert isinstance(output.security, MetadataTags), "did not receive data for security extractor"

        assert (
            "https://google.com" not in client.app.cache_backend._store
        ), "should not be cached, as it was not a complete result"

        with mock.patch(
            "features.accessibility.Accessibility._execute_api_call",
            new=AsyncMock(side_effect=lambda website_data, session, strategy: 0.1337),
        ):
            # now we should get a fully populated result (now Errors within the individual extractors)
            # which should also get cached.
            response = client.post(
                "/extract",
                data=Input(url="https://google.com").json(),
                timeout=10,
            )

            # make sure, that our result actually complies with the promised open api spec.
            output = Output.parse_obj(json.loads(response.text))

            pprint.pprint(output.dict())

            assert response.status_code == 200
            assert (
                "https://google.com" in client.app.cache_backend._store
            ), "should be cached, as it was a complete result"

            assert output.url == "https://google.com"
            assert isinstance(output.security, MetadataTags), "did not receive data for security extactor"
            # This should not be present, as the request to the accessibility container will fail
            assert isinstance(
                output.accessibility, MetadataTags
            ), "received accessibility result but container should not be running"
