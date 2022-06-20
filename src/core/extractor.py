import abc
import asyncio
import itertools
import logging
import os
import re
from collections import OrderedDict
from concurrent.futures import Executor
from enum import Enum
from logging import Logger
from typing import Generic, Optional, Type, TypeVar, Union
from urllib.parse import urlparse

import adblockparser
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from app.models import Explanation, StarCase
from core.website_manager import WebsiteData
from lib.settings import USE_LOCAL_IF_POSSIBLE
from lib.tools import runtime

T = TypeVar("T")


# Explanation strings
# fixme: Eventually migrate those to the respective extractors.
FOUND_LIST_MATCHES = "Found list matches"
FOUND_NO_LIST_MATCHES = "Found no list matches"
EMPTY_EXPLANATION = ""  # todo remove
NO_KNOCKOUT_MATCH_FOUND = "No knockout match found"
KNOCKOUT_MATCH_FOUND = "Found knockout match"
NO_EXPLANATION = "No explanation"  # todo remove


class Extractor(Generic[T]):
    key: str  # The name of the extracted metadatum

    @abc.abstractmethod
    async def setup(self):
        """
        Finish initialization of the extractor e.g. by downloading tag lists or other online resources.
        This method must be called for every newly created extractor to fully initialize it.
        """

    @abc.abstractmethod
    async def extract(self, site: WebsiteData, executor: Executor) -> tuple[StarCase, Explanation, T]:
        """
        Extract information from the website returning its star rating, an explanation and additional extractor specific
        information.
        :param site: The content to be analysed.
        :param executor: An executor to which CPU bound processing should be dispatched.
        """


async def download_tag_lists(session: ClientSession, urls: Union[str, list[str]], logger: Logger) -> set[str]:
    """
    Download tags from a list of urls and combine all downloaded tag lists into set removing all duplicates.
    :param session: The client to use for the downloads.
    :param urls: The urls from where to download individual tag lists.
    :param logger: Logger to be used.
    :return: The combined set of all tags.
    """

    def extract_dates(tags: list[str]) -> tuple[Optional[int], Optional[str]]:
        """
        Try to extract the expiration and last modification date from a downloaded tag list.
        :param tags: The individual lines of a downloaded tag list.
        :return: Tuple holding the expiration (in days?) and last modification date.
        """
        expires_expression = re.compile(r"[!#:]\sExpires[:=]\s?(\d+)\s?\w{0,4}")
        last_modified_expression = re.compile(r"[!#]\sLast modified:\s(\d\d\s\w{3}\s\d{4}\s\d\d:\d\d\s\w{3})")
        expiration = None
        last_modification = None
        # sometimes the first couple of lines of the downloaded
        # tag lists contain information about expiration and creation date.
        # checking the first lines would catch them if they are there and in
        # the expected format.
        for line in tags[0:10]:
            if match := last_modified_expression.match(line):
                last_modification = match.group(1)
            elif match := expires_expression.match(line):
                expiration = int(match.group(1))

            if last_modification is not None and expiration is not None:
                break
        return expiration, last_modification

    async def download_tags(url: str) -> tuple[Optional[int], Optional[str], set[str]]:
        taglist_path = "tag_lists/"
        if not os.path.isdir(taglist_path):
            os.makedirs(taglist_path, exist_ok=True)

        filename = os.path.basename(urlparse(url).path)
        if USE_LOCAL_IF_POSSIBLE and os.path.isfile(taglist_path + filename):
            with open(taglist_path + filename, "r") as file:
                tag_list = file.read().splitlines()
        else:
            result = await session.get(url=url)
            if result.status == 200:
                text = await result.text()
                tag_list = text.splitlines()
                if USE_LOCAL_IF_POSSIBLE:
                    with open(taglist_path + filename, "w+") as file:
                        file.write(text)
            else:
                raise RuntimeError(f"Downloading tag list from '{url}' yielded status code '{result.status}'.")

        expiration, last_modification = extract_dates(tag_list)
        logger.info(
            f"Downloaded tag list from {url=} with {len(tag_list)} entries and {expiration=}, {last_modification=}"
        )
        return expiration, last_modification, set(tag_list)

    # normalize urls argument into list[str]
    urls = [urls] if isinstance(urls, str) else urls
    tasks = [download_tags(url=url) for url in urls]
    tags: tuple[tuple[Optional[int], Optional[str], set[str]], ...] = await asyncio.gather(*tasks)
    # return set union, ignore expiration and last modification for now
    return set(itertools.chain(*(t for _, _, t in tags)))


class ProbabilityDeterminationMethod(Enum):
    NUMBER_OF_ELEMENTS = 1
    SINGLE_OCCURRENCE = 2
    FALSE_LIST = 3


class ExtractionMethod(Enum):
    MATCH_DIRECTLY = 1
    USE_ADBLOCK_PARSER = 2


class MetadataBase(Extractor[list[str]]):
    """
    Base class for features to be extracted.
    """

    tag_list: list = []
    false_list: list = []
    urls: list = []
    comment_symbol: str = ""
    evaluate_header: bool = False
    decision_threshold: float = -1
    probability_determination_method: ProbabilityDeterminationMethod = ProbabilityDeterminationMethod.SINGLE_OCCURRENCE
    extraction_method: ExtractionMethod = ExtractionMethod.MATCH_DIRECTLY
    match_rules = None

    adblockparser_options = {
        "script": True,
        "image": True,
        "stylesheet": True,
        "object": True,
        "xmlhttprequest": True,
        "object-subrequest": True,
        "subdocument": True,
        "document": True,
        "elemhide": True,
        "other": True,
        "background": True,
        "xbl": True,
        "ping": True,
        "dtd": True,
        "media": True,
        "third-party": True,
        "match-case": True,
        "collapse": True,
        "donottrack": True,
        "websocket": True,
        "domain": "",
    }

    @staticmethod
    def with_key(key: Optional[str] = None):
        """
        Provide the class with a key attribute.
        :param key: The key to use. Defaults to transformed snake_case of ClassName.
        :return: A decorator that adds a key attribute to the class.
        """

        def decorator(cls: Type["MetadataBase"]) -> Type["MetadataBase"]:
            cls.key = key or re.sub("" r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
            return cls

        return decorator

    def __init__(self, logger: Optional[Logger] = None):
        self._logger = logger or logging.getLogger(__name__)

    async def setup(self) -> None:
        """Fetch tag lists from configured urls."""

        if len(self.urls) > 0:
            if len(self.tag_list) != 0:
                raise RuntimeError("Cannot specify both urls and tag list")
            async with ClientSession() as session:
                self.tag_list = list(await download_tag_lists(urls=self.urls, session=session, logger=self._logger))

        if self.tag_list:
            self._prepare_tag_list()
            if self.extraction_method == ExtractionMethod.USE_ADBLOCK_PARSER:
                self.match_rules = adblockparser.AdblockRules(
                    self.tag_list, skip_unsupported_rules=False, use_re2=False
                )

    async def extract(self, site: WebsiteData, executor: Executor) -> tuple[StarCase, Explanation, T]:
        _, values, stars, explanation = await self.start(site)
        return stars, explanation, values

    @staticmethod
    def _get_ratio_of_elements(website_data: WebsiteData) -> tuple[float, Explanation]:
        if website_data.values and len(website_data.raw_links) > 0:
            ratio = round(len(website_data.values) / len(website_data.raw_links), 2)
            explanation = FOUND_LIST_MATCHES
        else:
            ratio = 0
            explanation = FOUND_NO_LIST_MATCHES
        return ratio, explanation

    def _calculate_probability_from_ratio(self, decision_indicator: float) -> float:
        return (
            round(
                abs((decision_indicator - self.decision_threshold) / (1 - self.decision_threshold)),
                2,
            )
            if self.decision_threshold != 1
            else 0
        )

    def _get_decision(self, probability: float) -> StarCase:
        decision = StarCase.ONE
        if probability >= 0 and self.decision_threshold != -1:
            if probability >= self.decision_threshold:
                decision = StarCase.ZERO
            else:
                decision = StarCase.FIVE
        return decision

    def _get_inverted_decision(self, probability: float) -> StarCase:
        decision = StarCase.ONE
        if probability > 0 and self.decision_threshold != -1:
            if probability <= self.decision_threshold:
                decision = StarCase.ZERO
            else:
                decision = StarCase.FIVE
        return decision

    def _decide(self, website_data: WebsiteData) -> tuple[StarCase, Explanation]:
        if self.probability_determination_method == ProbabilityDeterminationMethod.NUMBER_OF_ELEMENTS:
            decision_indicator, explanation = self._get_ratio_of_elements(website_data=website_data)
            star_case = self._get_decision(decision_indicator)
        elif self.probability_determination_method == ProbabilityDeterminationMethod.SINGLE_OCCURRENCE:
            (
                star_case,
                explanation,
            ) = self._decide_single_occurrence(website_data)
        elif self.probability_determination_method == ProbabilityDeterminationMethod.FALSE_LIST:
            star_case, explanation = self._decide_false_list(website_data)
        else:
            star_case, explanation = self._get_default_decision()

        return star_case, explanation

    def _decide_single_occurrence(self, website_data: WebsiteData) -> tuple[StarCase, Explanation]:

        an_occurence_has_been_found: bool = website_data.values and len(website_data.values) > 0
        explanation = FOUND_LIST_MATCHES if an_occurence_has_been_found else FOUND_NO_LIST_MATCHES
        star_case = StarCase.ZERO if an_occurence_has_been_found else StarCase.FIVE
        return star_case, explanation

    def _decide_false_list(self, website_data: WebsiteData) -> tuple[StarCase, Explanation]:
        decision = StarCase.FIVE
        explanation = NO_KNOCKOUT_MATCH_FOUND
        for false_element in self.false_list:
            if false_element in website_data.values:
                decision = StarCase.ZERO
                explanation = KNOCKOUT_MATCH_FOUND
                break

        return decision, explanation

    @staticmethod
    def _get_default_decision() -> tuple[StarCase, Explanation]:
        decision = StarCase.ZERO
        explanation = EMPTY_EXPLANATION
        return decision, explanation

    async def start(self, site: WebsiteData) -> tuple[float, list[str], StarCase, Explanation]:
        with runtime() as t:
            values = await self._start(website_data=site)
            site.values = values
            star_case, explanation = self._decide(website_data=site)
        return t(), values, star_case, explanation

    async def _start(self, website_data: WebsiteData) -> list[str]:
        if self.evaluate_header:
            return self._work_header(website_data.headers)
        else:
            return self._work_html_content(website_data)

    def _work_header(self, header: dict) -> list:
        values = []
        if len(self.tag_list) == 1:
            if self.tag_list[0] in header:
                values = header[self.tag_list[0]]
                if not isinstance(values, list):
                    values = [values]
        else:
            values = [header[ele] for ele in self.tag_list if ele in header]
        return values

    @staticmethod
    def _extract_raw_links(soup: BeautifulSoup) -> list:
        return list({a["href"] for a in soup.find_all(href=True)})

    def _parse_adblock_rules(self, website_data: WebsiteData) -> list:
        self.adblockparser_options["domain"] = website_data.domain
        values = [
            url
            for url in website_data.raw_links
            if self.match_rules.should_block(url=url, options=self.adblockparser_options)
        ]
        return values

    def _work_html_content(self, website_data: WebsiteData) -> list:
        values = []

        self._logger.info(f"Working on html content: {self.__class__.__name__}")
        if self.tag_list:
            if self.extraction_method == ExtractionMethod.MATCH_DIRECTLY:
                html = "".join(website_data.html.lower())
                values = [ele for ele in self.tag_list if ele in html]
            elif self.extraction_method == ExtractionMethod.USE_ADBLOCK_PARSER:
                values = self._parse_adblock_rules(website_data=website_data)

        return values

    def _prepare_tag_list(self) -> None:
        tag_list = [
            el.lower()
            for el in self.tag_list
            if el != "" and (self.comment_symbol == "" or not el.startswith(self.comment_symbol))
        ]

        self.tag_list = list(OrderedDict.fromkeys(tag_list))
