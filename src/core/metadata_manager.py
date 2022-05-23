import asyncio
import time
from typing import Optional, Type

from tldextract import TLDExtract

from app.communication import Message
from core.metadata_base import MetadataBase
from core.website_manager import WebsiteData
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
from lib.constants import EXPLANATION, STAR_CASE, TIME_REQUIRED, VALUES
from lib.logger import get_logger
from lib.timing import get_utc_now, global_start


class MetadataManager:
    def __init__(self, extractors: list[MetadataBase]) -> None:
        self._logger = get_logger()
        self.metadata_extractors = extractors
        self.tld_extractor: TLDExtract = TLDExtract(cache_dir=None)
        self.blacklisted_for_cache = [MaliciousExtensions, ExtractFromFiles, Javascript]

    @staticmethod
    async def create() -> "MetadataManager":
        extractors = [
            await MetadataManager._setup_extractor(get_logger(), extractor)
            for extractor in MetadataManager._extractors()
        ]
        return MetadataManager(extractors=extractors)

    @staticmethod
    async def _setup_extractor(logger, extractor_class: type(MetadataBase)) -> MetadataBase:
        logger.debug(f"Starting setup for {extractor_class} {get_utc_now()}")
        extractor = extractor_class(logger)
        await extractor.setup()
        logger.debug(f"Finished setup for {extractor_class} {get_utc_now()}")
        return extractor

    @classmethod
    def _extractors(cls) -> list[Type[MetadataBase]]:
        return [
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

    def is_feature_whitelisted_for_cache(self, extractor: type(MetadataBase)) -> bool:
        for feature in self.blacklisted_for_cache:
            if isinstance(extractor, feature):
                return False
        return True

    async def _extract_meta_data(
        self,
        site: WebsiteData,
        allow_list: Optional[list[str]],
    ) -> dict:
        data = {}
        tasks = []

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
                tasks.append(run_extractor_with_key(key=extractor.key, extractor=extractor, site=site))

        results: list[tuple[str, dict]] = await asyncio.gather(*tasks)

        # combine the cached results with the newly extracted data into the target dictionary structure
        return {
            **data,
            **{k: d for k, d in results},
        }

    async def start(self, message: Message) -> dict:
        self._logger.debug(f"Start metadata_manager at {time.perf_counter() - global_start} since start")

        # this will eventually load the content dynamically if not provided in the message
        # hence it may fail with various different exceptions (ConnectionError, ...)
        # those exceptions should be handled in the caller of this function.
        site = WebsiteData.from_message(
            message=message,
            logger=self._logger,
            tld_extractor=self.tld_extractor,
        )

        self._logger.debug(f"WebsiteManager loaded at {time.perf_counter() - global_start} since start")

        now = time.perf_counter()
        self._logger.debug(f"starting_extraction at {now - global_start} since start")
        starting_extraction = get_utc_now()
        extracted_meta_data = await self._extract_meta_data(site=site, allow_list=message.whitelist)

        self._logger.debug(f"extracted_meta_data at {time.perf_counter() - global_start} since start")
        extracted_meta_data.update(
            {
                "time_for_extraction": get_utc_now() - starting_extraction,
                "raw_links": site.raw_links,
                "image_links": site.image_links,
                "extensions": site.extensions,
            }
        )

        return extracted_meta_data
