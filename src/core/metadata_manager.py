import asyncio
import time
from multiprocessing import shared_memory
from typing import Optional

from tldextract import TLDExtract

from app.communication import Message
from app.models import Explanation
from cache.cache_manager import CacheManager
from core.metadata_base import MetadataBase
from core.website_manager import Singleton, WebsiteData
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
from lib.constants import ACCESSIBILITY, EXPLANATION, STAR_CASE, TIME_REQUIRED, TIMESTAMP, VALUES
from lib.logger import get_logger
from lib.timing import get_utc_now, global_start


@Singleton
class MetadataManager:
    metadata_extractors: list[type(MetadataBase)] = []

    blacklisted_for_cache = [MaliciousExtensions, ExtractFromFiles, Javascript]

    def __init__(self) -> None:
        self._logger = get_logger()
        self._setup_extractors()
        self.tld_extractor: TLDExtract = TLDExtract(cache_dir=None)

    def _setup_extractor(self, extractor_class: type(MetadataBase)) -> MetadataBase:
        self._logger.debug(f"Starting setup for {extractor_class} {get_utc_now()}")
        extractor = extractor_class(self._logger)
        extractor.setup()
        self._logger.debug(f"Finished setup for {extractor_class} {get_utc_now()}")
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

    def is_feature_whitelisted_for_cache(self, extractor: type(MetadataBase)) -> bool:
        for feature in self.blacklisted_for_cache:
            if isinstance(extractor, feature):
                return False
        return True

    async def _extract_meta_data(
        self,
        site: WebsiteData,
        allow_list: Optional[list[str]],
        cache_manager: CacheManager,
        shared_memory_name: str,
    ) -> dict:
        data = {}
        tasks = []

        shared_status = shared_memory.ShareableList(name=shared_memory_name)
        shared_status[0] = 0

        async def run_extractor_with_key(key: str, extractor: MetadataBase, site: WebsiteData) -> tuple[str, dict]:
            """Call the extractor and pack its results into a tuple containing also the key"""
            try:
                duration, values, stars, explanation = await extractor.start(site=site)
                return key, {
                    VALUES: values,
                    TIME_REQUIRED: duration,
                    STAR_CASE: stars,
                    EXPLANATION: explanation,
                }
            except Exception as e:
                self._logger.exception(f"Failed to extract from {key}: {e}")
                return key, {"exception": str(e)}

        for extractor in self.metadata_extractors:
            if allow_list is None or extractor.key in allow_list:
                if (
                    not cache_manager.bypass
                    and self.is_feature_whitelisted_for_cache(extractor)
                    and cache_manager.is_host_predefined()
                    and cache_manager.is_enough_cached_data_present(extractor.key)
                ):
                    extracted_metadata: dict = cache_manager.get_predefined_metadata(extractor.key)
                    data.update(extracted_metadata)
                    shared_status[0] += 1
                else:
                    tasks.append(run_extractor_with_key(key=extractor.key, extractor=extractor, site=site))

        results: list[tuple[str, dict]] = await asyncio.gather(*tasks)
        shared_status[0] += len(tasks)

        # combine the cached results with the newly extracted data into the target dictionary structure
        return {
            **data,
            **{k: d for k, d in results},
        }

    def cache_data(
        self,
        extracted_metadata: dict,
        cache_manager: CacheManager,
        allow_list: list[str],
    ):
        for feature, meta_data in extracted_metadata.items():
            if (allow_list is None or feature in allow_list) and Explanation.Cached not in meta_data[EXPLANATION]:
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

    def start(self, message: Message) -> dict:
        self._logger.debug(f"Start metadata_manager at {time.perf_counter() - global_start} since start")

        shared_status = shared_memory.ShareableList(name=message._shared_memory_name)
        url = message.url
        if len(url) > 1024:
            url = url[0:1024]
        shared_status[1] = url

        # this will eventually load the content dynamically if not provided in the message
        # hence it may fail with various different exceptions (ConnectionError, ...)
        # those exceptions should be handled in the caller of this function.
        site = WebsiteData.from_message(
            message=message,
            logger=self._logger,
            tld_extractor=self.tld_extractor,
        )

        self._logger.debug(f"WebsiteManager loaded at {time.perf_counter() - global_start} since start")
        cache_manager = CacheManager.get_instance()
        cache_manager.update_to_current_domain(
            site.domain,
            bypass=message.bypass_cache,
        )

        now = time.perf_counter()
        self._logger.debug(f"starting_extraction at {now - global_start} since start")
        starting_extraction = get_utc_now()
        extracted_meta_data = asyncio.run(
            self._extract_meta_data(
                site=site,
                allow_list=message.whitelist,
                cache_manager=cache_manager,
                shared_memory_name=message._shared_memory_name,
            )
        )
        self.cache_data(
            extracted_meta_data,
            cache_manager,
            allow_list=message.whitelist,
        )

        self._logger.debug(f"extracted_meta_data at {time.perf_counter() - global_start} since start")
        extracted_meta_data.update(
            {
                "time_for_extraction": get_utc_now() - starting_extraction,
                "raw_links": site.raw_links,
                "image_links": site.image_links,
                "extensions": site.extensions,
            }
        )

        cache_manager.reset()
        shared_status[1] = ""
        return extracted_meta_data
