import re
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum

import adblockparser
import requests
from bs4 import BeautifulSoup

from lib.constants import DECISION, PROBABILITY, VALUES
from lib.timing import get_utc_now


@dataclass
class MetadataData:
    html: str
    values: list = field(default_factory=list)
    headers: dict = field(default_factory=dict)


class ProbabilityDeterminationMethod(Enum):
    NUMBER_OF_ELEMENTS = 1
    SINGLE_OCCURRENCE = 2


class MetadataBase:
    tag_list: list = []
    tag_list_last_modified = ""
    tag_list_expires: int = 0
    key: str = ""
    url: str = ""
    urls: list = []
    comment_symbol: str = ""
    evaluate_header: bool = False
    decision_threshold: float = -1
    probability_determination_method: ProbabilityDeterminationMethod = (
        ProbabilityDeterminationMethod.SINGLE_OCCURRENCE
    )

    def __init__(self, logger) -> None:
        self._logger = logger

        if self.key == "":
            self.key = re.sub(
                r"(?<!^)(?=[A-Z])", "_", self.__class__.__name__
            ).lower()

    def _get_ratio_of_elements(self, values: list, html_content: str) -> float:
        soup = self._create_html_soup(html_content)
        raw_links = self._extract_raw_links(soup)

        if values and len(raw_links) > 0:
            ratio = len(values) / len(raw_links)
        else:
            ratio = 0
        return round(ratio, 2)

    def _calculate_probability(self, metadata: MetadataData) -> float:
        probability = -1
        if (
            self.probability_determination_method
            == ProbabilityDeterminationMethod.NUMBER_OF_ELEMENTS
        ):
            probability = self._get_ratio_of_elements(
                values=metadata.values, html_content=metadata.html
            )
        elif (
            self.probability_determination_method
            == ProbabilityDeterminationMethod.SINGLE_OCCURRENCE
        ):
            probability = (
                1 if (metadata.values and len(metadata.values) > 0) else 0
            )

        return probability

    def _decide(self, probability: float) -> bool:
        if self.decision_threshold == -1 or probability == -1:
            decision = None
        elif probability > self.decision_threshold:
            decision = True
        else:
            decision = False
        return decision

    def start(self, html_content: str = "", header=None) -> dict:
        metadata = MetadataData(html=html_content)
        if header is None:
            header = {}
        metadata.headers = header

        self._logger.info(f"Starting {self.__class__.__name__}")
        before = get_utc_now()
        values = self._start(metadata=metadata)

        metadata.values = values[VALUES]

        probability = self._calculate_probability(metadata=metadata)
        decision = self._decide(probability=probability)

        data = {
            self.key: {
                "time_required": get_utc_now() - before,
                **values,
                PROBABILITY: probability,
                DECISION: decision,
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

    def _work_header(self, header):
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
    def _create_html_soup(html_content: str) -> BeautifulSoup:
        return BeautifulSoup(html_content, "html.parser")

    @staticmethod
    def _extract_raw_links(soup: BeautifulSoup) -> list:
        return list({a["href"] for a in soup.find_all(href=True)})

    def _work_html_content(self, html_content) -> list:
        if self.tag_list:
            if self.url.find("easylist") >= 0:
                soup = self._create_html_soup(html_content)
                raw_links = self._extract_raw_links(soup)

                rules = adblockparser.AdblockRules(self.tag_list)
                values = []
                for url in raw_links:
                    is_blocked = rules.should_block(url)
                    if is_blocked:
                        values.append(url)
            else:
                values = [
                    ele for ele in self.tag_list if html_content.find(ele) >= 0
                ]
        else:
            values = []
        return values

    def _start(self, metadata: MetadataData) -> dict:
        if self.evaluate_header:
            values = self._work_header(metadata.headers)
        else:
            values = self._work_html_content(metadata.html)
        return {VALUES: values}

    def _download_multiple_tag_lists(self):
        complete_tag_list = []
        for url in self.urls:
            self.url = url
            self._download_tag_list()
            complete_tag_list.append(self.tag_list)

    def _download_tag_list(self) -> None:
        result = requests.get(self.url)
        if result.status_code == 200:
            self.tag_list = result.text.splitlines()
        else:
            self._logger.warning(
                f"Downloading tag list from '{self.url}' yielded status code '{result.status_code}'."
            )

    def _extract_date_from_list(self):
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
        self.tag_list = [i for i in self.tag_list if i != ""]

        self.tag_list = list(OrderedDict.fromkeys(self.tag_list))

        if self.comment_symbol != "":
            self.tag_list = [
                x
                for x in self.tag_list
                if not x.startswith(self.comment_symbol)
            ]

    def setup(self) -> None:
        """Child function."""
        if self.urls:
            self._download_multiple_tag_lists()
        elif self.url != "":
            self._download_tag_list()

        if self.tag_list:
            self._extract_date_from_list()
            self._prepare_tag_list()
