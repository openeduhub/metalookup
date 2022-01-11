import json
import logging
import time

from app.models import Explanation, StarCase
from db.db import (
    get_top_level_domains,
    read_cached_values_by_feature,
    reset_cache,
)
from features.website_manager import Singleton
from lib.constants import (
    ACCESSIBILITY,
    EXPLANATION,
    SECONDS_PER_DAY,
    STAR_CASE,
    TIME_REQUIRED,
    TIMESTAMP,
    VALUES,
)
from lib.logger import get_logger
from lib.settings import (
    BYPASS_CACHE,
    CACHE_RETENTION_TIME_DAYS,
    MINIMUM_REQUIRED_ENTRIES,
)
from lib.timing import get_utc_now, global_start
from lib.tools import get_mean, get_unique_list


@Singleton
class CacheManager:
    _logger: logging.Logger
    _domain: str
    _hosts: dict
    bypass: bool

    def __init__(self):
        super().__init__()
        self._logger = get_logger()
        self._logger.debug(
            f"CacheManager loaded at {time.perf_counter() - global_start} since start"
        )
        self.reset()
        self._prepare_cache_manager()

    def set_bypass(self, bypass: bool):
        self.bypass = bypass
        self._logger.debug(f"Bypass cache: {self.bypass}")

    def get_domain(self):
        return self._domain

    def set_domain(self, value: str):
        self._domain = value

    domain = property(get_domain, set_domain)

    def update_to_current_domain(self, current_domain: str, bypass: bool):
        self.update_hosts()
        self._domain = current_domain
        self.set_bypass(bypass)

    def update_hosts(self):
        self._hosts = get_top_level_domains()

    def _prepare_cache_manager(self) -> None:
        self._logger.debug(
            f"get_top_level_domains at {time.perf_counter() - global_start} since start"
        )
        self.update_hosts()
        self._logger.debug(
            f"get_top_level_domains done at {time.perf_counter() - global_start} since start"
        )

    def is_host_predefined(self) -> bool:
        return self._domain in self._hosts

    def is_enough_cached_data_present(self, key: str) -> bool:
        feature_values = read_cached_values_by_feature(key, self._domain)

        suitable_entries = 0
        for entry in feature_values:
            data = json.loads(entry)
            if self.is_cached_value_recent(data[TIMESTAMP]):
                suitable_entries += 1
            if suitable_entries >= MINIMUM_REQUIRED_ENTRIES:
                return True
        return False

    @staticmethod
    def is_cached_value_recent(timestamp: float) -> bool:
        return timestamp >= (
            get_utc_now() - CACHE_RETENTION_TIME_DAYS * SECONDS_PER_DAY
        )

    def convert_cached_data(self, meta_data: list, key: str) -> dict:
        values = []
        explanation = [Explanation.Cached]
        star_case = []
        for entry in meta_data:
            data = json.loads(entry)
            if self.is_cached_value_recent(data[TIMESTAMP]):
                values.extend(data[VALUES])
                explanation.extend(data[EXPLANATION])
                star_case.append(int(data[STAR_CASE]))

        explanation = get_unique_list(explanation)

        star_case = get_unique_list(star_case)
        if StarCase.ZERO in star_case:
            star_case = StarCase.ZERO
        elif StarCase.ONE in star_case:
            star_case = StarCase.ONE
        elif StarCase.FIVE in star_case:
            star_case = StarCase.FIVE
        else:
            star_case = StarCase.ONE

        if key == ACCESSIBILITY and len(values) > 0:
            values = [round(get_mean(values), 2)]
        else:
            values = []

        return {
            VALUES: values,
            EXPLANATION: get_unique_list(explanation),
            STAR_CASE: star_case,
        }

    def get_predefined_metadata(self, key: str) -> dict:
        feature_values = read_cached_values_by_feature(key, self._domain)
        converted_data = self.convert_cached_data(feature_values, key=key)

        meta_data = {key: converted_data}
        meta_data[key].update({TIME_REQUIRED: 0})
        return meta_data

    @staticmethod
    def reset_cache(domain: str):
        return reset_cache(domain)

    def reset(self):
        self._domain = ""
        self.bypass = BYPASS_CACHE
        self._hosts = {}
