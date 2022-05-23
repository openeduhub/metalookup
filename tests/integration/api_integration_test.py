import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import Input, app
from app.models import Error, Output
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
    response = client.post("/extract_meta", data=input.json(), timeout=10)

    import pprint

    pprint.pprint(response.json())

    assert response.status_code == 200

    # make sure, that our result actually complies with the promised open api spec.
    output = Output.parse_obj(json.loads(response.text))
    assert output.url == input.url
    # This should not be present, as the request to the accessibility container will fail
    assert isinstance(output.accessibility, Error), "received accessibility result but container should not be running"
