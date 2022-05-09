import asyncio
import time
import traceback
from collections import ChainMap
from multiprocessing import shared_memory

from app.models import Explanation
from cache.cache_manager import CacheManager
from core.metadata_base import MetadataBase
from core.website_manager import Singleton, WebsiteManager
from db.db import create_cache_entry
from features.accessibility import Accessibility
from features.cookies import Cookies
from features.extract_from_files import ExtractFromFiles
from features.gdpr import GDPR
from features.html_based import (
    Advertisement,
    AntiAdBlock,
    EasylistAdult,
    EasylistGermany,
    EasyPrivacy,
    FanboyAnnoyance,
    FanboyNotification,
    FanboySocialMedia,
    IFrameEmbeddable,
    LogInOut,
    Paywalls,
    PopUp,
    RegWall,
)
from features.javascript import Javascript
from features.malicious_extensions import MaliciousExtensions
from features.metatag_explorer import MetatagExplorer
from features.security import Security
from lib.constants import (
    ACCESSIBILITY,
    EXPLANATION,
    MESSAGE_ALLOW_LIST,
    MESSAGE_BYPASS_CACHE,
    MESSAGE_EXCEPTION,
    MESSAGE_SHARED_MEMORY_NAME,
    MESSAGE_URL,
    STAR_CASE,
    TIMESTAMP,
    VALUES,
)
from lib.logger import get_logger
from lib.timing import get_utc_now, global_start


@Singleton
class MetadataManager:
    metadata_extractors: list[type(MetadataBase)] = []

    blacklisted_for_cache = [MaliciousExtensions, ExtractFromFiles, Javascript]

    def __init__(self) -> None:
        self._logger = get_logger()
        self._setup_extractors()

    def _setup_extractor(
        self, extractor_class: type(MetadataBase)
    ) -> MetadataBase:
        self._logger.debug(
            f"Starting setup for {extractor_class} {get_utc_now()}"
        )
        extractor = extractor_class(self._logger)
        extractor.setup()
        self._logger.debug(
            f"Finished setup for {extractor_class} {get_utc_now()}"
        )
        return extractor

    def _setup_extractors(self) -> None:

        extractors = [
            Advertisement,
            EasyPrivacy,
            MaliciousExtensions,
            ExtractFromFiles,
            FanboyAnnoyance,
            FanboyNotification,
            FanboySocialMedia,
            AntiAdBlock,
            EasylistGermany,
            EasylistAdult,
            Paywalls,
            Security,
            IFrameEmbeddable,
            PopUp,
            RegWall,
            LogInOut,
            Cookies,
            GDPR,
            Javascript,
            MetatagExplorer,
            Accessibility,
        ]

        self.metadata_extractors: list[type(MetadataBase)] = [
            self._setup_extractor(extractor) for extractor in extractors
        ]

    def is_feature_whitelisted_for_cache(
        self, extractor: type(MetadataBase)
    ) -> bool:
        for feature in self.blacklisted_for_cache:
            if isinstance(extractor, feature):
                return False
        return True

    async def _extract_meta_data(
        self,
        allow_list: dict,
        cache_manager: CacheManager,
        shared_memory_name: str,
    ) -> dict:
        data = {}
        tasks = []

        shared_status = shared_memory.ShareableList(name=shared_memory_name)
        shared_status[0] = 0

        for metadata_extractor in self.metadata_extractors:
            if allow_list[metadata_extractor.key]:
                if (
                    not cache_manager.bypass
                    and self.is_feature_whitelisted_for_cache(
                        metadata_extractor
                    )
                    and cache_manager.is_host_predefined()
                    and cache_manager.is_enough_cached_data_present(
                        metadata_extractor.key
                    )
                ):
                    extracted_metadata: dict = (
                        cache_manager.get_predefined_metadata(
                            metadata_extractor.key
                        )
                    )
                    data.update(extracted_metadata)
                    shared_status[0] += 1
                elif metadata_extractor.call_async:
                    tasks.append(metadata_extractor.astart())
                else:
                    data.update(metadata_extractor.start())
                    shared_status[0] += 1

        extracted_metadata: tuple[dict] = await asyncio.gather(*tasks)
        shared_status[0] += len(tasks)
        data = {**data, **dict(ChainMap(*extracted_metadata))}
        return data

    def cache_data(
        self,
        extracted_metadata: dict,
        cache_manager: CacheManager,
        allow_list: dict,
    ):
        for feature, meta_data in extracted_metadata.items():
            if (
                allow_list[feature]
                and Explanation.Cached not in meta_data[EXPLANATION]
            ):
                values = []
                if feature == ACCESSIBILITY:
                    values = meta_data[VALUES]

                data_to_be_cached = {
                    VALUES: values,
                    STAR_CASE: meta_data[STAR_CASE],
                    TIMESTAMP: get_utc_now(),
                    EXPLANATION: meta_data[EXPLANATION],
                }

                create_cache_entry(
                    cache_manager.get_domain(),
                    feature,
                    data_to_be_cached,
                    self._logger,
                )

    def start(self, message: dict) -> dict:

        self._logger.debug(
            f"Start metadata_manager at {time.perf_counter() - global_start} since start"
        )

        shared_status = shared_memory.ShareableList(
            name=message[MESSAGE_SHARED_MEMORY_NAME]
        )
        url = message[MESSAGE_URL]
        if len(url) > 1024:
            url = url[0:1024]
        shared_status[1] = url

        website_manager = WebsiteManager.get_instance()
        self._logger.debug(
            f"WebsiteManager initialized at {time.perf_counter() - global_start} since start"
        )
        website_manager.load_website_data(message=message)

        self._logger.debug(
            f"WebsiteManager loaded at {time.perf_counter() - global_start} since start"
        )
        cache_manager = CacheManager.get_instance()
        cache_manager.update_to_current_domain(
            website_manager.website_data.domain,
            bypass=message[MESSAGE_BYPASS_CACHE],
        )

        now = time.perf_counter()
        self._logger.debug(
            f"starting_extraction at {now - global_start} since start"
        )
        starting_extraction = get_utc_now()
        if website_manager.website_data.html == "":
            exception = "Empty html. Potentially, splash failed."
            extracted_meta_data = {MESSAGE_EXCEPTION: exception}
        else:
            try:
                extracted_meta_data = asyncio.run(
                    self._extract_meta_data(
                        allow_list=message[MESSAGE_ALLOW_LIST],
                        cache_manager=cache_manager,
                        shared_memory_name=message[MESSAGE_SHARED_MEMORY_NAME],
                    )
                )
                self.cache_data(
                    extracted_meta_data,
                    cache_manager,
                    allow_list=message[MESSAGE_ALLOW_LIST],
                )
            except ConnectionError as e:
                exception = f"Connection error extracting metadata: '{e.args}'"
                self._logger.exception(
                    exception,
                    exc_info=True,
                )
                extracted_meta_data = {MESSAGE_EXCEPTION: exception}
            except Exception as e:
                exception = (
                    f"Unknown exception from extracting metadata: '{e.args}'. "
                    f"{''.join(traceback.format_exception(None, e, e.__traceback__))}"
                )
                self._logger.exception(
                    exception,
                    exc_info=True,
                )
                extracted_meta_data = {MESSAGE_EXCEPTION: exception}

        self._logger.debug(
            f"extracted_meta_data at {time.perf_counter() - global_start} since start"
        )
        extracted_meta_data.update(
            {
                "time_for_extraction": get_utc_now() - starting_extraction,
                **website_manager.get_website_data_to_log(),
            }
        )

        website_manager.reset()
        cache_manager.reset()
        shared_status[1] = ""

        self._logger.debug(
            f"website_manager.reset() at {time.perf_counter() - global_start} since start"
        )
        return extracted_meta_data
