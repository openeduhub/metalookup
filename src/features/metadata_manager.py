import asyncio
import multiprocessing
import time
import traceback
from collections import ChainMap
from itertools import repeat
from logging import Logger
from multiprocessing import shared_memory

from adblockparser.parser import _is_re2_supported

from app.models import Explanation
from cache.cache_manager import CacheManager
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
from features.metadata_base import MetadataBase
from features.metatag_explorer import MetatagExplorer
from features.security import Security
from features.website_manager import Singleton, WebsiteManager
from lib.constants import (
    ACCESSIBILITY,
    EXPLANATION,
    IS_HAPPY_CASE,
    MESSAGE_ALLOW_LIST,
    MESSAGE_BYPASS_CACHE,
    MESSAGE_SHARED_MEMORY_NAME,
    MESSAGE_URL,
    PROBABILITY,
    TIMESTAMP,
    VALUES,
)
from lib.logger import get_logger
from lib.timing import get_utc_now, global_start


def _parallel_setup(
    extractor_class: type(MetadataBase), logger: Logger
) -> MetadataBase:
    logger.debug(f"Starting setup for {extractor_class} {get_utc_now()}")
    extractor = extractor_class(logger)
    extractor.setup()
    logger.debug(f"Finished setup for {extractor_class} {get_utc_now()}")
    return extractor


def parallel_tasks(extractor: MetadataBase, logger):
    logger.debug(f"parallel_tasks: {extractor}")
    return extractor.start()


@Singleton
class MetadataManager:
    metadata_extractors: list[type(MetadataBase)] = []

    blacklisted_for_cache = [MaliciousExtensions, ExtractFromFiles, Javascript]

    def __init__(self) -> None:
        self._logger = get_logger()
        self._setup_extractors()

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

        self._logger.debug(f"re2: {_is_re2_supported()}")
        print(f"re2: {_is_re2_supported()}")

        before = get_utc_now()
        for extractor in extractors:
            self._logger.debug(f"extractor: {extractor}")
            self.metadata_extractors.append(
                _parallel_setup(extractor, self._logger)
            )
        self._logger.debug(
            f"self.metadata_extractors: {self.metadata_extractors}"
        )
        after = get_utc_now()
        self._logger.debug(
            f"Finished pool setup {after}, took {after - before}s."
        )
        """
        before = get_utc_now()
        self._logger.debug(f"Starting pool setup {get_utc_now()}")

        pool = multiprocessing.Pool(processes=6)
        self.metadata_extractors: list[type(MetadataBase)] = pool.starmap(
            _parallel_setup, zip(extractors, repeat(self._logger))
        )
        after = get_utc_now()
        self._logger.debug(f"Finished pool setup {after}, took {after - before}s.")
        """

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
        pool_tasks = []

        shared_status = shared_memory.ShareableList(name=shared_memory_name)
        shared_status[0] = 0

        for metadata_extractor in self.metadata_extractors:
            if allow_list[metadata_extractor.key]:
                self._logger.debug(f"Working on {metadata_extractor.key}")
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
                elif metadata_extractor.key == "advertisement" or metadata_extractor.key == "easy_privacy":
                    self._logger.debug(f"Bypass for {metadata_extractor}")
                    data.update(metadata_extractor.start())
                else:
                    pool_tasks.append(metadata_extractor)

        #self._logger.debug(f"setup before gather {time.perf_counter() - global_start} since start")
        self._logger.debug(f"pool_tasks {time.perf_counter() - global_start} since start: {pool_tasks}")

        # extracted_metadata: tuple[dict] = await asyncio.gather(*tasks)
        #self._logger.debug(f"setup after gather {time.perf_counter() - global_start} since start")

        self._logger.debug(f"setup before pool {time.perf_counter() - global_start} since start.")
        pool = multiprocessing.Pool(processes=10)

        try:
            extracted_metadata = pool.starmap(parallel_tasks, zip(pool_tasks, repeat(self._logger)))
        except Exception as e:
            extracted_metadata = {}
            self._logger.debug(f"3: {e.args}")
            for task in pool_tasks:
                self._logger.debug(f"Task: {task}")
                self._logger.debug(f"Task.start: {task.start()}")
        self._logger.debug(f"setup after pool {time.perf_counter() - global_start} since start")
        self._logger.debug(
            f"setup after pool2 {time.perf_counter() - global_start} since start: {extracted_metadata}")

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
                    PROBABILITY: meta_data[PROBABILITY],
                    IS_HAPPY_CASE: meta_data[IS_HAPPY_CASE],
                    TIMESTAMP: get_utc_now(),
                    EXPLANATION: meta_data[EXPLANATION],
                }

                create_cache_entry(
                    cache_manager.domain,
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
        cache_manager.update_domains()
        cache_manager.domain = website_manager.website_data.domain
        cache_manager.set_bypass(message[MESSAGE_BYPASS_CACHE])
        self._logger.debug(f"Bypass cache: {cache_manager.bypass}")

        now = time.perf_counter()
        self._logger.debug(
            f"starting_extraction at {now - global_start} since start"
        )
        starting_extraction = get_utc_now()
        if website_manager.website_data.html == "":
            exception = "Empty html. Potentially, splash failed."
            extracted_meta_data = {"exception": exception}
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
                extracted_meta_data = {"exception": exception}
            except Exception as e:
                exception = (
                    f"Unknown exception from extracting metadata: '{e.args}'. "
                    f"{''.join(traceback.format_exception(None, e, e.__traceback__))}"
                )
                self._logger.exception(
                    exception,
                    exc_info=True,
                )
                extracted_meta_data = {"exception": exception}

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
        shared_status[1] = ""

        self._logger.debug(
            f"website_manager.reset() at {time.perf_counter() - global_start} since start"
        )
        return extracted_meta_data
