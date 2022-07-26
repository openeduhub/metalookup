import asyncio
import logging
from concurrent.futures import ProcessPoolExecutor
from typing import Type, Union

from aiohttp import ClientError
from fastapi import HTTPException
from pydantic import ValidationError

from metalookup.app.models import Error, Input, MetadataTags, Output
from metalookup.core.content import Content
from metalookup.core.extractor import Extractor
from metalookup.features.accessibility import Accessibility
from metalookup.features.adblock_based import (
    Advertisement,
    AntiAdBlock,
    EasylistAdult,
    EasylistGermany,
    EasyPrivacy,
    FanboyAnnoyance,
    FanboyNotification,
    FanboySocialMedia,
)
from metalookup.features.cookies import Cookies
from metalookup.features.direct_match import LogInOut, Paywalls, PopUp, RegWall
from metalookup.features.extract_from_files import ExtractFromFiles
from metalookup.features.gdpr import GDPR
from metalookup.features.iframe import IFrameEmbeddable
from metalookup.features.javascript import Javascript
from metalookup.features.licence import LicenceExtractor
from metalookup.features.malicious_extensions import MaliciousExtensions
from metalookup.features.security import Security
from metalookup.lib.tools import runtime


class MetadataManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # will be initialized in setup call - use None here so that extraction
        # fails if setup method was not called as required
        self.extractors: list[Extractor] = None  # noqa

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

        if message.splash_response is None:
            content = Content(url=message.url)
        else:
            content = Content(url=message.url, html=message.splash_response.html, har=message.splash_response.har)

        async def run_extractor(extractor: Extractor) -> Union[MetadataTags, Error]:
            """Call the extractor and transform its result into the expected output format"""
            try:
                with runtime() as t:
                    stars, explanation, extra_data = await extractor.extract(
                        content=content, executor=self.process_pool
                    )
                self.logger.info(f"Extracted {extractor.__class__.__name__} in {t():5.2f}s.")
                return MetadataTags(stars=stars, explanation=explanation, extra=extra_data if extra else None)
            except Exception as e:
                self.logger.exception(f"Failed to extract {extractor.key} for {message.url}")
                return Error(error=str(e))

        self.logger.debug("Dispatching extractor calls.")

        try:
            # The call to gather (with return_exceptions=False) fails if any of the submitted tasks raise an exception.
            # This is what we want, as we have to respond with an all or nothing result. I.e. we have metadata extracted
            # for all fields or none of them.
            results: tuple[Union[MetadataTags, Error], ...] = await asyncio.gather(
                *[run_extractor(extractor=extractor) for extractor in self.extractors]
            )
            self.logger.debug("Received all extractor results.")

            # fixme: Correctly Identify and handle within Content class:
            #        https://github.com/openeduhub/metalookup/issues/155
            #   - 404 page content
            #   - non-html urls
            # Make sure we didn't extract meta information from a 404 placeholder site or similar.
            # This happens after the calls to extractors to prevent awaiting splash and then awaiting the
            # extractors in sequential order.
            response_code = (await content.har()).log.entries[-1].response.status
            if response_code != 200:
                raise HTTPException(
                    status_code=502, detail=f"Resource could not be loaded by splash (reported: {response_code})"
                )

            return Output(url=message.url, **{e.key: v for e, v in zip(self.extractors, results)})

        # Technically, for the user the communication with the splash container (which will eventually happen
        # during the extractor calls) is an implementation detail of the server. Returning a 502 (Bad Gateway)
        # should indicate to the user, that the resource (in this case the url that was transmitted to the extract
        # endpoint) is no longer available, whereas internal communication problems should not give this indication
        # to the user.
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Could not get HAR from splash: {e}")
        except asyncio.exceptions.TimeoutError:
            raise HTTPException(status_code=500, detail="Splash container request timeout.")
        except ValidationError as e:
            raise HTTPException(status_code=500, detail=f"Received unexpected HAR from splash: {e}")
