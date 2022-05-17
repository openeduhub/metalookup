import json
import multiprocessing
import os
import threading
import time
from unittest import mock

import pytest
import requests
import uvicorn

from app.api import Input, app
from app.models import Output
from lib.settings import API_PORT
from tests.test_libs import DOCKER_TEST_HEADERS, DOCKER_TEST_URL

"""
--------------------------------------------------------------------------------
"""


def _start_api(send_message, get_message):
    app.communicator = mock.MagicMock()
    app.communicator.send_message = send_message
    app.communicator.get_message = get_message
    uvicorn.run(app, host="0.0.0.0", port=API_PORT, log_level="info")


def test_ping_container():
    api_to_manager_queue = multiprocessing.Queue()
    manager_to_api_queue = multiprocessing.Queue()

    with mock.patch("app.api.create_request_record"):
        with mock.patch("app.api.create_response_record"):
            api_process = multiprocessing.Process(
                target=_start_api,
                args=(api_to_manager_queue, manager_to_api_queue),
            )
            api_process.start()
            time.sleep(0.1)

            response = requests.request(
                "GET",
                DOCKER_TEST_URL + "_ping",
                headers=DOCKER_TEST_HEADERS,
                timeout=1,
            )
            api_process.terminate()
            api_process.join()

    data = json.loads(response.text)
    is_ok = data["status"] == "ok"
    assert is_ok


"""
--------------------------------------------------------------------------------
"""


@pytest.mark.skipif(
    "CI" in os.environ,
    reason="Skip this test on the github CI as it causes problems there.",
)
def test_extract_meta_container(mocker):
    send_message = mocker.MagicMock()
    send_message.return_value = 3
    get_message = mocker.MagicMock()
    get_message.return_value = {"meta": "empty"}

    with mock.patch("app.api.create_request_record"):
        with mock.patch("app.api.create_response_record"):

            api_process = multiprocessing.Process(
                target=_start_api,
                args=(send_message, get_message),
            )
            api_process.start()
            time.sleep(0.1)

            input_data = Input(url="https://google.com")

            response = requests.request(
                "POST",
                DOCKER_TEST_URL + "extract_meta",
                data=json.dumps(input_data.json()),
                headers=DOCKER_TEST_HEADERS,
                timeout=3,
            )
            api_process.terminate()
            api_process.join()

    assert (
        response.ok
    ), f"Received response {response} is not OK. {response.text}"
    # make sure, that our result actually complies with the promised open api spec.
    data = Output.parse_obj(json.loads(response.text))
    print(data)

    assert data.url == input_data.url
