import json
import multiprocessing
import os
import time
from unittest import mock

import requests
import uvicorn

from app.api import Input, app
from lib.settings import API_PORT

if "PRE_COMMIT" in os.environ:
    from test_libs import DOCKER_TEST_HEADERS, DOCKER_TEST_URL
else:
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
        timeout=60,
    )
    api_process.terminate()
    api_process.join()

    data = json.loads(response.text)
    is_ok = data["status"] == "ok"
    assert is_ok


"""
--------------------------------------------------------------------------------
"""


def test_extract_meta_container(mocker):
    send_message = mocker.MagicMock()
    send_message.return_value = 3
    get_message = mocker.MagicMock()
    get_message.return_value = {"meta": "empty"}
    api_process = multiprocessing.Process(
        target=_start_api,
        args=(send_message, get_message),
    )
    api_process.start()
    time.sleep(0.1)

    url = "useless_url"
    input_data = Input(url=url).__dict__
    input_data["allow_list"] = input_data["allow_list"].__dict__

    response = requests.request(
        "POST",
        DOCKER_TEST_URL + "extract_meta",
        data=json.dumps(input_data),
        headers=DOCKER_TEST_HEADERS,
        timeout=3,
    )
    api_process.terminate()
    api_process.join()

    data = json.loads(response.text)

    assert data["url"] == url
    assert len(data["url"]) == 11
