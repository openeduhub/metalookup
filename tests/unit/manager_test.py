from unittest import mock

import pytest

from core.website_manager import WebsiteManager
from lib.settings import WANT_PROFILING
from manager import Manager


@pytest.fixture
def manager(mocker):
    Manager._create_api = mocker.MagicMock()

    with mock.patch("manager.Manager.run"):
        with mock.patch("manager.MetadataManager"):
            with mock.patch("manager.create_logger"):
                manager = Manager()

    return manager


"""
--------------------------------------------------------------------------------
"""


def test_init(manager: Manager, mocker):
    run_spy = mocker.spy(manager, "run")
    assert manager._logger.call_count == 0
    assert manager._create_api.call_count == 1
    assert run_spy.call_count == 0
    assert manager.run_loop


"""
--------------------------------------------------------------------------------
"""


def test_run(manager: Manager, mocker):
    manager.run = Manager.run
    manager._handle_api_request = mocker.MagicMock()

    manager.run_loop = False
    manager.run(manager)
    assert manager._handle_api_request.call_count == 0


"""
--------------------------------------------------------------------------------
"""


def test_handle_content(manager: Manager, mocker):
    request = {}

    empty_header = "empty_header"
    empty_html = "empty_html"
    empty_url = "empty_url"

    manager._handle_content(request)

    assert (
        manager.metadata_manager.get_instance().load_website_data.call_count
        == 0
    )
    assert manager.metadata_manager.get_instance().reset.call_count == 0

    allow_list = {}
    request = {
        "some_uuid": {
            "html": empty_html,
            "headers": empty_header,
            "allow_list": allow_list,
            "url": empty_url,
        }
    }

    manager.manager_to_api_queue = mocker.MagicMock()
    manager.metadata_manager = mocker.MagicMock()

    assert WANT_PROFILING is False

    manager._handle_content(request)

    assert manager.metadata_manager.start.call_count == 1

    is_extract_meta_data_called_with_empty_html = (
        manager.metadata_manager.start.call_args_list[0][1]
        == {"message": request["some_uuid"]}
    )
    assert is_extract_meta_data_called_with_empty_html

    website_manager = WebsiteManager.get_instance()
    website_manager.reset()
