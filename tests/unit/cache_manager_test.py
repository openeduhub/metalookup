import json
from unittest import mock

import pytest

from app.models import DecisionCase, Explanation
from cache.cache_manager import CacheManager
from lib.constants import (
    ACCESSIBILITY,
    EXPLANATION,
    IS_HAPPY_CASE,
    PROBABILITY,
    TIMESTAMP,
    VALUES,
)
from lib.timing import get_utc_now


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


"""
--------------------------------------------------------------------------------
"""


def test_is_enough_cached_data_present(cache_manager: CacheManager):
    cache_entries = [f'{{"timestamp": {get_utc_now()}}}'] * 1
    with mock.patch(
        "cache.cache_manager.read_cached_values_by_feature"
    ) as read_cache:
        read_cache.return_value = cache_entries
        assert (
            cache_manager.is_enough_cached_data_present(ACCESSIBILITY) is False
        )

    cache_entries = [f'{{"timestamp": {get_utc_now()}}}'] * 5
    with mock.patch(
        "cache.cache_manager.read_cached_values_by_feature"
    ) as read_cache:
        read_cache.return_value = cache_entries
        assert (
            cache_manager.is_enough_cached_data_present(ACCESSIBILITY) is True
        )


"""
--------------------------------------------------------------------------------
"""


def test_convert_cached_data(cache_manager: CacheManager):
    meta_data = []
    feature = ACCESSIBILITY

    empty_cache = cache_manager.convert_cached_data(meta_data, feature)
    assert empty_cache[EXPLANATION] == [Explanation.Cached]
    assert empty_cache[IS_HAPPY_CASE] == DecisionCase.UNKNOWN
    assert empty_cache[VALUES] == []
    assert empty_cache[PROBABILITY] == 0

    meta_data = [
        f'{{"{VALUES}":[], "{PROBABILITY}": 1.0, "{EXPLANATION}": ["{Explanation.AccessibilityServiceReturnedFailure}"], '
        f'"{IS_HAPPY_CASE}": "{DecisionCase.UNKNOWN}", '
        f'"{TIMESTAMP}": {get_utc_now()}}}'
    ]

    cache_output = cache_manager.convert_cached_data(meta_data, feature)
    assert isinstance(cache_output, dict)
    assert len(cache_output.keys()) == 4
    assert cache_output[EXPLANATION] == [
        Explanation.Cached,
        Explanation.AccessibilityServiceReturnedFailure,
    ]
    assert cache_output[IS_HAPPY_CASE] == DecisionCase.UNKNOWN
    assert cache_output[VALUES] == []
    assert cache_output[PROBABILITY] == 1.0

    meta_data = [
        f'{{"{VALUES}":[], "{PROBABILITY}": 0, "{EXPLANATION}": [], '
        f'"{IS_HAPPY_CASE}": "{DecisionCase.FALSE}", '
        f'"{TIMESTAMP}": {get_utc_now()}}}'
    ]

    cache_output = cache_manager.convert_cached_data(meta_data, feature)
    assert cache_output[IS_HAPPY_CASE] == DecisionCase.FALSE

    meta_data = [
        f'{{"{VALUES}":[0.85, 0.95], "{PROBABILITY}": 1.0, "{EXPLANATION}": ["{Explanation.AccessibilitySuitable}"], '
        f'"{IS_HAPPY_CASE}": "{DecisionCase.UNKNOWN}", '
        f'"{TIMESTAMP}": {get_utc_now()}}}'
    ]

    cache_output = cache_manager.convert_cached_data(meta_data, feature)
    assert cache_output[VALUES] == [0.9]
    assert cache_output[EXPLANATION] == [
        Explanation.Cached,
        Explanation.AccessibilitySuitable,
    ]

    meta_data = [
        f'{{"{VALUES}":[], "{PROBABILITY}": 0, "{EXPLANATION}": [], '
        f'"{IS_HAPPY_CASE}": "{DecisionCase.TRUE}", '
        f'"{TIMESTAMP}": {get_utc_now()}}}'
    ]

    cache_output = cache_manager.convert_cached_data(meta_data, feature)
    assert cache_output[IS_HAPPY_CASE] == DecisionCase.TRUE


"""
--------------------------------------------------------------------------------
"""


def test_get_predefined_metadata(mocker, cache_manager: CacheManager):
    meta_data = []
    feature = ACCESSIBILITY

    empty_cache = cache_manager.convert_cached_data(meta_data, feature)
    assert empty_cache[EXPLANATION] == [Explanation.Cached]
    assert empty_cache[IS_HAPPY_CASE] == DecisionCase.UNKNOWN
    assert empty_cache[VALUES] == []
    assert empty_cache[PROBABILITY] == 0

    meta_data = (
        f'{{"{VALUES}":[], "{PROBABILITY}": 1.0, "{EXPLANATION}": ["{Explanation.AccessibilityServiceReturnedFailure}"], '
        + f'"{IS_HAPPY_CASE}": "{DecisionCase.UNKNOWN}"}}'
    )

    with mock.patch("cache.cache_manager.read_cached_values_by_feature"):
        cache_manager.convert_cached_data = mocker.MagicMock()
        cache_manager.convert_cached_data.return_value = json.loads(meta_data)
        cache_output = cache_manager.get_predefined_metadata(feature)
    print(cache_output)
    assert isinstance(cache_output, dict)
    assert len(cache_output.keys()) == 1
    assert len(cache_output[feature].keys()) == 5
