import asyncio
import json
import os
from logging import Logger
from unittest import mock
from unittest.mock import AsyncMock

import pytest
from integration.features_integration_test import mock_website_data

from app.communication import Message
from app.models import Explanation, StarCase
from cache.cache_manager import CacheManager
from core import website_manager
from core.metadata_manager import MetadataManager
from features import accessibility
from features.html_based import Advertisement
from features.javascript import Javascript
from lib.constants import (
    ACCESSIBILITY,
    EXPLANATION,
    MESSAGE_EXCEPTION,
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


@pytest.mark.skipif(
    "CI" in os.environ,
    reason="Skip this test on the github CI as it causes problems there.",
)
def test_extract_meta_data(metadata_manager: MetadataManager):
    paywall = "paywall"
    allow_list = ["accessibility", "paywall"]
    cache_manager = get_cache_manager()

    extractor_backup = metadata_manager.metadata_extractors
    metadata_manager.metadata_extractors = [
        extractor
        for extractor in metadata_manager.metadata_extractors
        if extractor.key in allow_list
    ]
    test_host = "test_host"
    cache_manager._hosts = []
    cache_manager.domain = test_host
    site = mock_website_data()

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
                    site, allow_list, cache_manager, "test"
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
                        site, allow_list, cache_manager, "test"
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


def test_start(metadata_manager: MetadataManager):
    cache_manager = get_cache_manager()

    cache_manager._hosts = []
    cache_manager.domain = "google.com"

    message = Message(
        extractors=None,
        bypass_cache=False,
        html=None,
        header=None,
        url="https://google.com",
        _shared_memory_name="test",
        har={},
    )

    with open("spash-response-google.json", "r") as f:
        splash_response = json.load(f)

    async def accessibility_api_call_mock(
        self, website_data, session, strategy
    ) -> float:  # noqa
        return 0.98

    with mock.patch(
        "core.metadata_manager.shared_memory.ShareableList"
    ) as shareable_list:
        with mock.patch(
            "cache.cache_manager.CacheManager._class.update_to_current_domain"
        ):
            with mock.patch(
                "core.metadata_manager.MetadataManager._class.cache_data"
            ):
                # intercept the request to the non-running splash
                # container and lighthouse container
                # and instead use the checked in response json and a hardcoded
                # score value
                with mock.patch("requests.get"), mock.patch(
                    "json.loads", lambda _: splash_response
                ), mock.patch(
                    "features.accessibility.Accessibility._execute_api_call",
                    accessibility_api_call_mock,
                ):
                    shareable_list.return_value = [0, ""]
                    output = metadata_manager.start(message)

                    print("Extraction result from manager:")
                    print(output)

                    assert MESSAGE_EXCEPTION not in output.keys()
                    assert "time_for_extraction" in output.keys()

                    # check that all extractors worked without exceptions
                    for k, v in filter(
                        lambda i: isinstance(i, dict), output.items()
                    ):
                        assert (
                            "exception" not in v
                        ), f"Extractor {k} failed with {v['exception']}"
