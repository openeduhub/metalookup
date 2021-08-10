import json
import logging
import time

from psycopg2 import ProgrammingError

import db.models as db_models
from app.models import DecisionCase, Explanation
from db.db import SessionLocal, get_top_level_domains, reset_cache
from features.website_manager import Singleton
from lib.constants import (
    ACCESSIBILITY,
    EXPLANATION,
    IS_HAPPY_CASE,
    PROBABILITY,
    SECONDS_PER_DAY,
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

    def __init__(self):
        super().__init__()
        self.domain: str = ""
        self._hosts = {}
        self._logger = get_logger()
        self._logger.debug(
            f"CacheManager loaded at {time.perf_counter() - global_start} since start"
        )
        self.bypass = BYPASS_CACHE
        self._prepare_cache_manager()

    def set_bypass(self, bypass: bool):
        self.bypass = bypass

    def get_domain(self):
        return self._domain

    def set_domain(self, value: str):
        self._domain = value

    domain = property(get_domain, set_domain)

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
        feature_values = self.read_cached_feature_values(key)

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
        probability = []
        explanation = [Explanation.Cached]
        decision = []
        for entry in meta_data:
            data = json.loads(entry)
            if self.is_cached_value_recent(data[TIMESTAMP]):
                values.extend(data[VALUES])
                probability.append(data[PROBABILITY])
                explanation.extend(data[EXPLANATION])
                decision.append(data[IS_HAPPY_CASE])

        explanation = get_unique_list(explanation)

        decision = get_unique_list(decision)
        if DecisionCase.FALSE in decision:
            decision = DecisionCase.FALSE
        elif DecisionCase.UNKNOWN in decision:
            decision = DecisionCase.UNKNOWN
        elif DecisionCase.TRUE in decision:
            decision = DecisionCase.TRUE
        else:
            decision = DecisionCase.UNKNOWN

        values = []
        if key == ACCESSIBILITY and len(values) > 0:
            values = [get_mean(values)]

        return {
            VALUES: values,
            EXPLANATION: get_unique_list(explanation),
            PROBABILITY: get_mean(probability),
            IS_HAPPY_CASE: decision,
        }

    def read_cached_feature_values(self, key: str) -> list:
        database = SessionLocal()
        try:
            entry = (
                database.query(db_models.CacheEntry)
                    .filter_by(top_level_domain=self._domain)
                    .first()
            )
        except (ProgrammingError, AttributeError) as e:
            self._logger.exception(f"Reading cache failed: {e.args}")
            entry = []
        if entry is None:
            return []
        return entry.__getattribute__(key)

    def get_predefined_metadata(self, key: str) -> dict:
        feature_values = self.read_cached_feature_values(key)
        converted_data = self.convert_cached_data(feature_values, key=key)

        meta_data = {key: converted_data}
        meta_data[key].update(
            {
                TIME_REQUIRED: 0,
                EXPLANATION: converted_data[EXPLANATION],
            }
        )
        return meta_data

    @staticmethod
    def reset_cache(domain: str):
        return reset_cache(domain)
