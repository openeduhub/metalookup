import json
import logging

import db.models as db_models
from app.models import DecisionCase, Explanation
from db.db import SessionLocal, get_top_level_domains, load_cache
from features.website_manager import Singleton
from lib.constants import (
    ACCESSIBILITY,
    DECISION,
    EXPLANATION,
    PROBABILITY,
    SECONDS_PER_DAY,
    TIME_REQUIRED,
    TIMESTAMP,
    VALUES,
)
from lib.logger import create_logger
from lib.settings import CACHE_RETENTION_TIME_DAYS, MINIMUM_REQUIRED_ENTRIES
from lib.timing import get_utc_now
from lib.tools import get_mean, get_unique_list


@Singleton
class CacheManager:
    _logger: logging.Logger

    def __init__(self):
        super().__init__()
        self.top_level_domain: str = ""
        self.hosts = {}
        self._logger = create_logger()
        self._prepare_cache_manager()

    def _prepare_cache_manager(self) -> None:
        self.hosts = get_top_level_domains()

    def is_host_predefined(self) -> bool:
        return self.top_level_domain in self.hosts

    def is_enough_cached_data_present(self, key: str) -> bool:
        feature_values = self.read_cached_feature_values(key)

        suitable_entries = 0
        for entry in feature_values:
            data = json.loads(entry)
            if self.is_cached_value_recent(data[TIMESTAMP]):
                suitable_entries += 1
            if suitable_entries >= MINIMUM_REQUIRED_ENTRIES:
                break

        return suitable_entries >= MINIMUM_REQUIRED_ENTRIES

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
                decision.extend(data[DECISION])

        explanation = get_unique_list(explanation)

        decision = get_unique_list(decision)
        if DecisionCase.FALSE in decision:
            decision = DecisionCase.FALSE
        elif DecisionCase.UNKNOWN in decision:
            decision = DecisionCase.UNKNOWN
        else:
            decision = DecisionCase.TRUE

        if key == ACCESSIBILITY:
            values = [get_mean(values)]
        else:
            values = []

        return {
            VALUES: values,
            EXPLANATION: get_unique_list(explanation),
            PROBABILITY: get_mean(probability),
            DECISION: decision,
        }

    def read_cached_feature_values(self, key: str) -> list:
        database = SessionLocal()
        entry = (
            database.query(db_models.CacheEntry)
            .filter_by(top_level_domain=self.top_level_domain)
            .first()
        )
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
