import json

import pytest
import requests
from test_libs import (
    DOCKER_TEST_HEADERS,
    DOCKER_TEST_URL,
    _build_and_run_docker,
)


@pytest.mark.skip(
    reason="This test takes a lot of time, depending on payload etc. Execute manually."
)
def test_ping_container():
    url = DOCKER_TEST_URL + "_ping"

    _build_and_run_docker()

    response = requests.request(
        "GET", url, headers=DOCKER_TEST_HEADERS, timeout=60
    )

    data = json.loads(response.text)
    is_ok = data["status"] == "ok"
    assert is_ok
