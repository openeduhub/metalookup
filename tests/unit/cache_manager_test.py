import json
from unittest import mock

import pytest

from app.models import Explanation, StarCase
from cache.cache_manager import CacheManager
from lib.constants import ACCESSIBILITY, EXPLANATION, STAR_CASE, TIMESTAMP, VALUES
from lib.timing import get_utc_now


@pytest.fixture()
def cache() -> CacheManager:
    return CacheManager()


"""
--------------------------------------------------------------------------------
"""


def test_is_host_predefined(cache: CacheManager):
    assert cache.is_host_predefined() is False

    test_host = "test_host"
    cache._hosts = [test_host]
    cache.domain = test_host

    assert cache.is_host_predefined()


"""
--------------------------------------------------------------------------------
"""


def test_is_enough_cached_data_present(cache: CacheManager):
    cache_entries = [f'{{"timestamp": {get_utc_now()}}}'] * 1
    with mock.patch("cache.cache_manager.read_cached_values_by_feature") as read_cache:
        read_cache.return_value = cache_entries
        assert cache.is_enough_cached_data_present(ACCESSIBILITY) is False

    cache_entries = [f'{{"timestamp": {get_utc_now()}}}'] * 5
    with mock.patch("cache.cache_manager.read_cached_values_by_feature") as read_cache:
        read_cache.return_value = cache_entries
        assert cache.is_enough_cached_data_present(ACCESSIBILITY) is True


"""
--------------------------------------------------------------------------------
"""


def test_convert_cached_data(cache: CacheManager):
    meta_data = []
    feature = ACCESSIBILITY

    empty_cache = cache.convert_cached_data(meta_data, feature)
    assert empty_cache[EXPLANATION] == [Explanation.Cached]
    assert empty_cache[STAR_CASE] == StarCase.ONE
    assert empty_cache[VALUES] == []

    meta_data = [
        f'{{"{VALUES}":[], "{EXPLANATION}": ["{Explanation.AccessibilityServiceReturnedFailure}"], '
        f'"{STAR_CASE}": "{StarCase.ONE}", '
        f'"{TIMESTAMP}": {get_utc_now()}}}'
    ]

    cache_output = cache.convert_cached_data(meta_data, feature)
    assert isinstance(cache_output, dict)
    assert len(cache_output.keys()) == 3
    assert cache_output[EXPLANATION] == [
        Explanation.Cached,
        Explanation.AccessibilityServiceReturnedFailure,
    ]
    assert cache_output[STAR_CASE] == StarCase.ONE
    assert cache_output[VALUES] == []

    meta_data = [
        f'{{"{VALUES}":[], "{EXPLANATION}": [], '
        f'"{STAR_CASE}": "{StarCase.ONE}", '
        f'"{TIMESTAMP}": {get_utc_now()}}}'
    ]

    cache_output = cache.convert_cached_data(meta_data, feature)
    assert cache_output[STAR_CASE] == StarCase.ONE

    meta_data = [
        f'{{"{VALUES}":[0.85, 0.95], "{EXPLANATION}": ["{Explanation.AccessibilitySuitable}"], '
        f'"{STAR_CASE}": "{StarCase.ONE}", '
        f'"{TIMESTAMP}": {get_utc_now()}}}'
    ]

    cache_output = cache.convert_cached_data(meta_data, feature)
    assert cache_output[VALUES] == [0.9]
    assert cache_output[EXPLANATION] == [
        Explanation.Cached,
        Explanation.AccessibilitySuitable,
    ]

    meta_data = [
        f'{{"{VALUES}":[], "{EXPLANATION}": [], '
        f'"{STAR_CASE}": "{StarCase.FIVE}", '
        f'"{TIMESTAMP}": {get_utc_now()}}}'
    ]

    cache_output = cache.convert_cached_data(meta_data, feature)
    assert cache_output[STAR_CASE] == StarCase.FIVE


"""
--------------------------------------------------------------------------------
"""


def test_get_predefined_metadata(mocker, cache: CacheManager):
    meta_data = []
    feature = ACCESSIBILITY

    empty_cache = cache.convert_cached_data(meta_data, feature)
    assert empty_cache[EXPLANATION] == [Explanation.Cached]
    assert empty_cache[STAR_CASE] == StarCase.ONE
    assert empty_cache[VALUES] == []

    meta_data = (
        f'{{"{VALUES}":[], "{EXPLANATION}": ["{Explanation.AccessibilityServiceReturnedFailure}"], '
        + f'"{STAR_CASE}": "{StarCase.ONE}"}}'
    )

    with mock.patch("cache.cache_manager.read_cached_values_by_feature"):
        cache.convert_cached_data = mocker.MagicMock()
        cache.convert_cached_data.return_value = json.loads(meta_data)
        cache_output = cache.get_predefined_metadata(feature)

    assert isinstance(cache_output, dict)
    assert len(cache_output.keys()) == 1
    assert len(cache_output[feature].keys()) == 4
