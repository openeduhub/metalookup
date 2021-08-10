from unittest import mock

import pytest

from cache.cache_manager import CacheManager


@pytest.fixture
def cache_manager(mocker):
    with mock.patch("cache.cache_manager.get_logger"):
        with mock.patch(
            "cache.cache_manager.CacheManager._class._prepare_cache_manager"
        ):
            manager = CacheManager.get_instance()

    return manager


"""
--------------------------------------------------------------------------------
"""


def test_init(mocker):
    with mock.patch("cache.cache_manager.get_logger"):
        with mock.patch(
            "cache.cache_manager.CacheManager._class._prepare_cache_manager"
        ) as prepare_cache_manager:
            manager = CacheManager.get_instance()
            assert manager._logger.debug.call_count == 1
            assert prepare_cache_manager.call_count == 1


"""
--------------------------------------------------------------------------------
"""


def test_is_host_predefined(cache_manager: CacheManager):
    assert cache_manager.is_host_predefined() is False

    test_host = "test_host"
    cache_manager._hosts = [test_host]
    cache_manager.domain = test_host

    assert cache_manager.is_host_predefined()

