import asyncio
import logging
from concurrent.futures import ProcessPoolExecutor
from typing import Type, Union

from aiohttp import ClientConnectorError
from fastapi import HTTPException
from pydantic import ValidationError
from tldextract import TLDExtract

from app.models import Error, Input, MetadataTags, Output
from core.extractor import Extractor
from core.website_manager import WebsiteData
from features.accessibility import Accessibility
from features.addblock_based import (
    Advertisement,
    AntiAdBlock,
    EasylistAdult,
    EasylistGermany,
    EasyPrivacy,
    FanboyAnnoyance,
    FanboyNotification,
    FanboySocialMedia,
)
from features.cookies import Cookies
from features.extract_from_files import ExtractFromFiles
from features.gdpr import GDPR
from features.html_based import IFrameEmbeddable, LogInOut, Paywalls, PopUp, RegWall
from features.javascript import Javascript
from features.licence import LicenceExtractor
from features.malicious_extensions import MaliciousExtensions
from features.metatag_explorer import MetatagExplorer
from features.security import Security
from lib.tools import runtime


class MetadataManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # will be initialized in setup call - use None here so that extraction
        # fails if setup method was not called as required
        self.extractors: list[Extractor] = None  # noqa
        self.tld_extractor: TLDExtract = TLDExtract(cache_dir=None)

        # fixme: eventually we may want to shut down the process pool upon termination
        self.process_pool: ProcessPoolExecutor = ProcessPoolExecutor(max_workers=4)

    async def setup(self):
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
            LicenceExtractor,
        ]

        async def create_extractor(extractor: Type[Extractor]) -> Extractor:
            instance = extractor()
            await instance.setup()
            return instance

        logging.info("Initializing extractors")
        self.extractors: tuple[Extractor, ...] = await asyncio.gather(
            *[create_extractor(extractor) for extractor in types]
        )
        logging.info("Done initializing extractors")

    async def extract(self, message: Input, extra: bool) -> Output:
        """
        Call the different registered extractors concurrently with given input.
        :param message: The message holding URL and or HAR (splash response) to analyse. If no splash response
                        is contained the splash container will be queried before invoking the extractors.
        :param extra: If set to true, additional extractor specific information will be added to the output.
        """
        self.logger.debug("Calling extractors from manager")

        # this will eventually load the content dynamically if not provided in the message
        # hence it may fail with various different exceptions (ConnectionError, ...)
        # those exceptions should be handled in the caller of this function.
        try:
            with runtime() as t:
                site = await WebsiteData.from_input(
                    input=message,
                    logger=self.logger,
                    tld_extractor=self.tld_extractor,
                )
            self.logger.info(f"Built WebsiteData object in {t():5.2f}s.")
        except ClientConnectorError as e:
            raise HTTPException(status_code=502, detail=f"Could not get HAR from splash: {e}")
        except ValidationError as e:
            raise HTTPException(status_code=500, detail=f"Received unexpected HAR from splash: {e}")

        async def run_extractor(extractor: Extractor) -> Union[MetadataTags, Error]:
            """Call the extractor and transform its result into the expected output format"""
            try:
                with runtime() as t:
                    stars, explanation, extra_data = await extractor.extract(site=site, executor=self.process_pool)
                self.logger.info(f"Extracted {extractor.__class__.__name__} in {t():5.2f}s.")
                if extra:
                    return MetadataTags(stars=stars, explanation=explanation, extra=extra_data)
                return MetadataTags(stars=stars, explanation=explanation, extra=None)
            except Exception as e:
                self.logger.exception(f"Failed to extract {extractor.key}")
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
