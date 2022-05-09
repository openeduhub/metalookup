import asyncio
from logging import Logger
from unittest import mock
from unittest.mock import AsyncMock

import pytest

from app.models import Explanation, StarCase
from cache.cache_manager import CacheManager
from core.metadata_manager import MetadataManager
from features.html_based import Advertisement
from features.javascript import Javascript
from lib.constants import (
    ACCESSIBILITY,
    EXPLANATION,
    MESSAGE_ALLOW_LIST,
    MESSAGE_BYPASS_CACHE,
    MESSAGE_EXCEPTION,
    MESSAGE_HEADERS,
    MESSAGE_HTML,
    MESSAGE_SHARED_MEMORY_NAME,
    MESSAGE_URL,
    STAR_CASE,
    VALUES,
)
from lib.settings import NUMBER_OF_EXTRACTORS


@pytest.fixture
def metadata_manager():
    manager = MetadataManager.get_instance()
    return manager


"""
--------------------------------------------------------------------------------
"""


def test_init(metadata_manager: MetadataManager):
    assert isinstance(metadata_manager._logger, Logger)
    assert NUMBER_OF_EXTRACTORS == 21
    assert len(metadata_manager.metadata_extractors) == NUMBER_OF_EXTRACTORS


"""
--------------------------------------------------------------------------------
"""


def test_is_feature_whitelisted_for_cache(
    mocker, metadata_manager: MetadataManager
):
    assert metadata_manager.is_feature_whitelisted_for_cache(
        Advertisement(mocker.MagicMock())
    )
    assert (
        metadata_manager.is_feature_whitelisted_for_cache(
            Javascript(mocker.MagicMock())
        )
        is False
    )


"""
--------------------------------------------------------------------------------
"""


def get_cache_manager():
    with mock.patch("cache.cache_manager.get_logger"):
        with mock.patch(
            "cache.cache_manager.CacheManager._class._prepare_cache_manager"
        ):
            return CacheManager.get_instance()


def test_cache_data(metadata_manager: MetadataManager):
    meta_data = {
        ACCESSIBILITY: {
            EXPLANATION: [],
            VALUES: [],
            STAR_CASE: StarCase.ONE,
        }
    }
    allow_list = {ACCESSIBILITY: True}
    cache_manager = get_cache_manager()

    with mock.patch(
        "core.metadata_manager.create_cache_entry"
    ) as create_cache_entry:
        metadata_manager.cache_data(meta_data, cache_manager, allow_list)
        assert create_cache_entry.call_args[0][2][VALUES] == []
        assert create_cache_entry.call_count == 1


"""
--------------------------------------------------------------------------------
"""


def test_extract_meta_data(metadata_manager: MetadataManager):
    paywall = "paywall"
    allow_list = {ACCESSIBILITY: True, paywall: True}
    cache_manager = get_cache_manager()

    extractor_backup = metadata_manager.metadata_extractors
    metadata_manager.metadata_extractors = [
        extractor
        for extractor in metadata_manager.metadata_extractors
        if extractor.key in allow_list.keys()
    ]
    test_host = "test_host"
    cache_manager._hosts = []
    cache_manager.domain = test_host

    with mock.patch(
        "core.metadata_manager.shared_memory.ShareableList"
    ) as shareable_list:
        with mock.patch(
            "cache.cache_manager.CacheManager._class.is_enough_cached_data_present"
        ) as is_enough_cached_data_present:
            is_enough_cached_data_present.return_value = True
            shareable_list.return_value = [0, ""]
            extracted_meta_data = asyncio.run(
                metadata_manager._extract_meta_data(
                    allow_list, cache_manager, "test"
                )
            )

    assert ACCESSIBILITY in extracted_meta_data.keys()
    assert extracted_meta_data[ACCESSIBILITY][EXPLANATION] == [
        Explanation.none
    ]
    assert paywall in extracted_meta_data.keys()
    assert extracted_meta_data[paywall][EXPLANATION] == [
        Explanation.FoundNoListMatches
    ]

    test_host = "test_host"
    cache_manager._hosts = [test_host]
    cache_manager.domain = test_host

    with mock.patch(
        "core.metadata_manager.shared_memory.ShareableList"
    ) as shareable_list:
        with mock.patch(
            "cache.cache_manager.CacheManager._class.is_enough_cached_data_present"
        ) as is_enough_cached_data_present:
            with mock.patch(
                "cache.cache_manager.CacheManager._class.get_predefined_metadata"
            ) as get_predefined_metadata:
                is_enough_cached_data_present.return_value = True
                get_predefined_metadata.return_value = {
                    ACCESSIBILITY: {EXPLANATION: [Explanation.Cached]},
                    paywall: {EXPLANATION: [Explanation.Cached]},
                }
                shareable_list.return_value = [0, ""]
                extracted_meta_data = asyncio.run(
                    metadata_manager._extract_meta_data(
                        allow_list, cache_manager, "test"
                    )
                )

    assert ACCESSIBILITY in extracted_meta_data.keys()
    assert extracted_meta_data[ACCESSIBILITY][EXPLANATION] == [
        Explanation.Cached
    ]
    assert paywall in extracted_meta_data.keys()
    assert extracted_meta_data[paywall][EXPLANATION] == [Explanation.Cached]

    metadata_manager.metadata_extractors = extractor_backup


"""
--------------------------------------------------------------------------------
"""


def test_start(mocker, metadata_manager: MetadataManager):
    cache_manager = get_cache_manager()

    test_host = "test_host"
    cache_manager._hosts = []
    cache_manager.domain = test_host

    message = {
        MESSAGE_SHARED_MEMORY_NAME: "test",
        MESSAGE_URL: "empty_url",
        MESSAGE_BYPASS_CACHE: "f",
        MESSAGE_ALLOW_LIST: {},
        MESSAGE_HTML: "test_html",
        MESSAGE_HEADERS: "",
    }
    log_spy = mocker.spy(metadata_manager, "_logger")

    with mock.patch(
        "core.metadata_manager.shared_memory.ShareableList"
    ) as shareable_list:
        with mock.patch(
            "core.metadata_manager.WebsiteManager"
        ) as website_manager:
            with mock.patch(
                "cache.cache_manager.CacheManager._class.update_to_current_domain"
            ):
                async_mock = AsyncMock(return_value={})
                with mock.patch(
                    "core.metadata_manager.MetadataManager._class._extract_meta_data",
                    side_effect=async_mock,
                ) as extract_meta_data:
                    with mock.patch(
                        "core.metadata_manager.MetadataManager._class.cache_data"
                    ):
                        with mock.patch(
                            "core.metadata_manager.WebsiteManager._class.load_website_data"
                        ):
                            website_manager.get_instance().website_data.html = (
                                "non-empty html"
                            )
                            shareable_list.return_value = [0, ""]
                            output = metadata_manager.start(message)

                            assert MESSAGE_EXCEPTION not in output.keys()
                            assert "time_for_extraction" in output.keys()
                            assert log_spy.debug.call_count == 6
                            assert log_spy.exception.call_count == 0

                            extract_meta_data.side_effect = ConnectionError
                            output = metadata_manager.start(message)

                            assert MESSAGE_EXCEPTION in output.keys()
                            assert (
                                "Connection error extracting metadata:"
                                in output[MESSAGE_EXCEPTION]
                            )
                            assert log_spy.exception.call_count == 1

                            extract_meta_data.side_effect = Exception
                            output = metadata_manager.start(message)

                            assert MESSAGE_EXCEPTION in output.keys()
                            assert (
                                "Unknown exception from extracting metadata:"
                                in output[MESSAGE_EXCEPTION]
                            )
                            assert log_spy.exception.call_count == 2

                            website_manager.get_instance().website_data.html = (
                                ""
                            )
                            output = metadata_manager.start(message)
                            assert MESSAGE_EXCEPTION in output.keys()
                            assert (
                                "Empty html. Potentially, splash failed."
                                in output[MESSAGE_EXCEPTION]
                            )

                            website_manager.reset()
