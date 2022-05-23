import asyncio
import logging
from typing import Type, Union

from tldextract import TLDExtract

from app.models import Error, Input, MetadataTags, Output
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
from lib.logger import get_logger


class MetadataManager:
    def __init__(self, extractors: list[MetadataBase]):
        self.logger = get_logger()
        self.extractors = extractors
        self.tld_extractor: TLDExtract = TLDExtract(cache_dir=None)

    @classmethod
    async def create(cls) -> "MetadataManager":
        types = [
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

        async def create_extractor(Extractor: Type[MetadataBase]) -> MetadataBase:  # noqa
            instance = Extractor()
            await instance.setup()
            return instance

        logging.info("Initializing extractors")
        extractors: tuple[MetadataBase, ...] = await asyncio.gather(
            *[create_extractor(extractor) for extractor in types]
        )
        logging.info("Creating MetadataManager")
        return MetadataManager(extractors=list(extractors))

    async def extract(self, message: Input) -> Output:
        self.logger.debug("Calling extractors from manager")

        # this will eventually load the content dynamically if not provided in the message
        # hence it may fail with various different exceptions (ConnectionError, ...)
        # those exceptions should be handled in the caller of this function.
        site = await WebsiteData.from_input(
            input=message,
            logger=self.logger,
            tld_extractor=self.tld_extractor,
        )

        self.logger.debug("Build website data object.")

        async def run_extractor(extractor: MetadataBase) -> Union[MetadataTags, Error]:
            """Call the extractor and transform its result into the expected output format"""
            try:
                _, _, stars, explanation = await extractor.start(site=site)
                return MetadataTags(stars=stars, explanation=explanation)
            except Exception as e:
                return Error(error=str(e))

        self.logger.debug("Dispatching extractor calls.")

        # The call to gather (with return_exceptions=False) fails if any of the submitted tasks raise an exception.
        # This is what we want, as we have to respond with an all or nothing result. I.e. we have metadata extracted
        # for all fields or none of them.
        results: tuple[Union[MetadataTags, Error], ...] = await asyncio.gather(
            *[run_extractor(extractor=extractor) for extractor in self.extractors]
        )
        self.logger.debug("Received all extractor results.")

        return Output(url=message.url, **{e.key: v for e, v in zip(self.extractors, results)})
