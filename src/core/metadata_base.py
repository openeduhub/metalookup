import asyncio
import os
import re
from collections import OrderedDict
from enum import Enum
from logging import Logger
from typing import Optional, Type
from urllib.parse import urlparse

import adblockparser
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from app.models import Explanation, StarCase
from core.website_manager import WebsiteData, WebsiteManager
from lib.constants import EXPLANATION, STAR_CASE, TIME_REQUIRED, VALUES
from lib.settings import USE_LOCAL_IF_POSSIBLE
from lib.timing import get_utc_now


class ProbabilityDeterminationMethod(Enum):
    NUMBER_OF_ELEMENTS = 1
    SINGLE_OCCURRENCE = 2
    FALSE_LIST = 3


class ExtractionMethod(Enum):
    MATCH_DIRECTLY = 1
    USE_ADBLOCK_PARSER = 2


class MetadataBase:
    """
    Base class for features to be extracted.
    """

    tag_list: list = []
    tag_list_last_modified = ""
    tag_list_expires: int = 0
    false_list: list = []
    url: str = ""
    urls: list = []
    comment_symbol: str = ""
    evaluate_header: bool = False
    decision_threshold: float = -1
    probability_determination_method: ProbabilityDeterminationMethod = (
        ProbabilityDeterminationMethod.SINGLE_OCCURRENCE
    )
    extraction_method: ExtractionMethod = ExtractionMethod.MATCH_DIRECTLY
    call_async: bool = False
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
            cls.key = (
                key or re.sub("" r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
            )
            return cls

        return decorator

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    @staticmethod
    def _get_ratio_of_elements(
        website_data: WebsiteData,
    ) -> tuple[float, list[Explanation]]:
        if website_data.values and len(website_data.raw_links) > 0:
            ratio = round(
                len(website_data.values) / len(website_data.raw_links), 2
            )
            explanation = [Explanation.FoundListMatches]
        else:
            ratio = 0
            explanation = [Explanation.FoundNoListMatches]
        return ratio, explanation

    def _calculate_probability_from_ratio(
        self, decision_indicator: float
    ) -> float:
        return (
            round(
                abs(
                    (decision_indicator - self.decision_threshold)
                    / (1 - self.decision_threshold)
                ),
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

    def _decide(
        self, website_data: WebsiteData
    ) -> tuple[StarCase, list[Explanation]]:
        if (
            self.probability_determination_method
            == ProbabilityDeterminationMethod.NUMBER_OF_ELEMENTS
        ):
            decision_indicator, explanation = self._get_ratio_of_elements(
                website_data=website_data
            )
            star_case = self._get_decision(decision_indicator)
        elif (
            self.probability_determination_method
            == ProbabilityDeterminationMethod.SINGLE_OCCURRENCE
        ):
            (
                star_case,
                explanation,
            ) = self._decide_single_occurrence(website_data)
        elif (
            self.probability_determination_method
            == ProbabilityDeterminationMethod.FALSE_LIST
        ):
            star_case, explanation = self._decide_false_list(website_data)
        else:
            star_case, explanation = self._get_default_decision()

        return star_case, explanation

    def _decide_single_occurrence(
        self, website_data: WebsiteData
    ) -> tuple[StarCase, list[Explanation]]:

        an_occurence_has_been_found: bool = (
            website_data.values and len(website_data.values) > 0
        )
        explanation = (
            [Explanation.FoundListMatches]
            if an_occurence_has_been_found
            else [Explanation.FoundNoListMatches]
        )
        star_case = (
            StarCase.ZERO if an_occurence_has_been_found else StarCase.FIVE
        )
        return star_case, explanation

    def _decide_false_list(
        self, website_data: WebsiteData
    ) -> tuple[StarCase, list[Explanation]]:
        decision = StarCase.FIVE
        explanation = [Explanation.NoKnockoutMatchFound]
        for false_element in self.false_list:
            if false_element in website_data.values:
                decision = StarCase.ZERO
                explanation = [Explanation.KnockoutMatchFound]
                break

        return decision, explanation

    @staticmethod
    def _get_default_decision() -> tuple[StarCase, list[Explanation]]:
        decision = StarCase.ZERO
        explanation = [Explanation.none]
        return decision, explanation

    @staticmethod
    def _prepare_website_data() -> WebsiteData:
        website_manager = WebsiteManager.get_instance()
        return website_manager.website_data

    def _processing_values(
        self, values: list[str], website_data: WebsiteData, before: float
    ) -> dict:
        website_data.values = values

        star_case, explanation = self._decide(website_data=website_data)

        data = {
            self.key: {
                TIME_REQUIRED: get_utc_now() - before,
                VALUES: values,
                STAR_CASE: star_case,
                EXPLANATION: explanation,
            }
        }
        if self.tag_list_last_modified != "":
            data[self.key].update(
                {
                    "tag_list_last_modified": self.tag_list_last_modified,
                    "tag_list_expires": self.tag_list_expires,
                }
            )
        return data

    def _prepare_start(self) -> tuple[float, WebsiteData]:
        self._logger.info(f"Starting {self.__class__.__name__}.")
        before = get_utc_now()
        website_data = self._prepare_website_data()
        return before, website_data

    async def astart(self) -> dict:
        before, website_data = self._prepare_start()
        values = await self._astart(website_data=website_data)
        return self._processing_values(
            values=values, website_data=website_data, before=before
        )

    def start(self) -> dict:
        before, website_data = self._prepare_start()
        values = self._start(website_data=website_data)
        return self._processing_values(
            values=values, website_data=website_data, before=before
        )

    async def _astart(self, website_data: WebsiteData) -> list[str]:
        return self._work_html_content(website_data=website_data)

    def _start(self, website_data: WebsiteData) -> list[str]:
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
            if self.match_rules.should_block(
                url=url, options=self.adblockparser_options
            )
        ]
        return values

    def _work_html_content(self, website_data: WebsiteData) -> list:
        values = []

        self._logger.info(
            f"Working on html content: {self.__class__.__name__},{len(self.tag_list)}"
        )
        if self.tag_list:
            if self.extraction_method == ExtractionMethod.MATCH_DIRECTLY:
                html = "".join(website_data.html.lower())
                values = [ele for ele in self.tag_list if ele in html]
            elif self.extraction_method == ExtractionMethod.USE_ADBLOCK_PARSER:
                values = self._parse_adblock_rules(website_data=website_data)

        return values

    async def _download_multiple_tag_lists(
        self, session: ClientSession
    ) -> list[str]:
        tasks = [
            self._download_tag_list(url=url, session=session)
            for url in self.urls
        ]
        tag_lists = await asyncio.gather(*tasks)
        complete_list = list(tag for tag_list in tag_lists for tag in tag_list)
        return complete_list

    async def _download_tag_list(
        self, url: str, session: ClientSession
    ) -> list[str]:
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
                self._logger.exception(
                    f"Downloading tag list from '{url}' yielded status code '{result.status}'."
                )
                tag_list = []
        return tag_list

    def _extract_date_from_list(self) -> None:
        expires_expression = re.compile(
            r"[!#:]\sExpires[:=]\s?(\d+)\s?\w{0,4}"
        )
        last_modified_expression = re.compile(
            r"[!#]\sLast modified:\s(\d\d\s\w{3}\s\d{4}\s\d\d:\d\d\s\w{3})"
        )
        for line in self.tag_list[0:10]:
            match = last_modified_expression.match(line)
            if match:
                self.tag_list_last_modified = match.group(1)

            match = expires_expression.match(line)
            if match:
                self.tag_list_expires = int(match.group(1))

            if (
                self.tag_list_last_modified != ""
                and self.tag_list_expires != 0
            ):
                break

    def _prepare_tag_list(self) -> None:
        tag_list = [
            el.lower()
            for el in self.tag_list
            if el != ""
            and (
                self.comment_symbol == ""
                or not el.startswith(self.comment_symbol)
            )
        ]

        self.tag_list = list(OrderedDict.fromkeys(tag_list))

    async def _setup_downloads(self) -> None:
        async with ClientSession() as session:
            if self.urls:
                self.tag_list = await self._download_multiple_tag_lists(
                    session=session
                )
            elif self.url != "":
                self.tag_list = await self._download_tag_list(
                    url=self.url, session=session
                )

    def setup(self) -> None:
        """Child function."""
        asyncio.run(self._setup_downloads())
        if self.tag_list:
            self._extract_date_from_list()
            self._prepare_tag_list()
            if self.extraction_method == ExtractionMethod.USE_ADBLOCK_PARSER:
                self.match_rules = adblockparser.AdblockRules(
                    self.tag_list, skip_unsupported_rules=False, use_re2=False
                )
