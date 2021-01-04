import json
from json import JSONDecodeError

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
def test_e2e():
    url = DOCKER_TEST_URL + "extract_meta"

    payload = '{"url": "https://digitallearninglab.de/unterrichtsbausteine/anlauttraining"}'

    _build_and_run_docker()

    response = requests.request(
        "POST", url, headers=DOCKER_TEST_HEADERS, data=payload, timeout=60
    )

    try:
        data = json.loads(response.text)
        is_json = True
    except JSONDecodeError:
        data = {}
        is_json = False
    has_url = "url" in data.keys()
    has_meta = "url" in data.keys()
    needs_less_than_a_minute = data["time_until_complete"] < 60

    assert is_json and has_url and has_meta and needs_less_than_a_minute
