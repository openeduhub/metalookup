import json
import logging

from sqlalchemy.engine import ChunkedIteratorResult

import db.models as db_models
from app.models import Explanation
from db.db import SessionLocal, get_top_level_domains, load_cache
from features.website_manager import Singleton
from lib.constants import EXPLANATION, TIME_REQUIRED
from lib.logger import create_logger


@Singleton
class ConfigManager:
    _logger: logging.Logger

    def __init__(self):
        super().__init__()
        self.top_level_domain: str = ""
        self.hosts = {}
        self._logger = create_logger()
        self._load_config()

    def _load_config(self) -> None:
        cache = load_cache()
        self._logger.debug(f"Cache: {cache}")
        self.hosts = get_top_level_domains()

    def is_host_predefined(self) -> bool:
        return self.top_level_domain in self.hosts

    def is_metadata_predefined(self, key: str) -> bool:
        return (
            key in self.hosts[self.top_level_domain].keys()
            if self.top_level_domain != ""
            and self.top_level_domain in self.hosts.keys()
            and key in self.hosts[self.top_level_domain].keys()
            else False
        )

    def get_predefined_metadata(self, key: str) -> dict:
        database = SessionLocal()
        entry = (
            database.query(db_models.CacheEntry)
            .filter_by(top_level_domain=self.top_level_domain)
            .first()
        )
        self._logger.debug(f"current tld: {self.top_level_domain}")
        self._logger.debug(f"cached tld: {entry}")
        feature_data = entry.__getattribute__(key)
        self._logger.debug(f"cached feature_data: {feature_data}")
        converted_data = json.loads(feature_data[0])
        self._logger.debug(f"cached converted_data: {converted_data}")

        meta_data = {key: converted_data}
        meta_data[key].update(
            {
                TIME_REQUIRED: 0,
                EXPLANATION: converted_data[EXPLANATION]
                + [Explanation.Cached],
            }
        )
        self._logger.debug(f"meta_data: {meta_data}")
        return meta_data
