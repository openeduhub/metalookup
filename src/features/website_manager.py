import json
import os
import re
import traceback
from dataclasses import dataclass, field
from json import JSONDecodeError
from typing import NoReturn
from urllib.parse import urlparse

import bs4
import requests
from bs4 import BeautifulSoup
from tldextract.suffix_list import SuffixListNotFound
from tldextract.tldextract import TLDExtract

from lib.constants import (
    MESSAGE_HAR,
    MESSAGE_HEADERS,
    MESSAGE_HTML,
    MESSAGE_URL,
)
from lib.logger import create_logger
from lib.settings import SPLASH_HEADERS, SPLASH_URL


@dataclass
class WebsiteData:
    html: str = field(default_factory=str)
    values: list = field(default_factory=list)
    headers: dict = field(default_factory=dict)
    raw_header: str = field(default_factory=str)
    soup: BeautifulSoup = field(default_factory=BeautifulSoup)
    raw_links: list = field(default_factory=list)
    image_links: list = field(default_factory=list)
    extensions: list = field(default_factory=list)
    url: str = field(default_factory=str)
    top_level_domain: str = field(default_factory=str)
    har: dict = field(default_factory=dict)


class Singleton:
    _instance = None

    def __init__(self, cls) -> None:
        self._class = cls

    def get_instance(self):
        if self._instance is None:
            self._instance = self._class()
        return self._instance

    def __call__(self) -> NoReturn:
        raise TypeError(
            "Singletons must only be accessed through `get_instance()`."
        )

    def __instancecheck__(self, inst) -> bool:
        return isinstance(inst, self._class)


@Singleton
class WebsiteManager:
    website_data: WebsiteData

    source_regex = re.compile(r"src\=[\"|\']([\w\d\:\/\.\-\?\=]+)[\"|\']")

    def __init__(self) -> None:
        super().__init__()
        self._logger = create_logger()

        try:
            self.tld_extractor = TLDExtract(cache_dir=False)
        except (ConnectionError, SuffixListNotFound) as e:
            self._logger.error(
                f"Cannot extract top_level_domain because '{e.args}'"
            )
            self.tld_extractor = None

        self.reset()

    def load_website_data(self, message: dict = None) -> None:
        if message is None:
            message = {}

        if self.website_data.url == "":
            self.website_data.url = message[MESSAGE_URL]
            self._extract_top_level_domain()

        if (
            self.website_data.raw_header == ""
            and message[MESSAGE_HEADERS] != ""
        ):
            self.website_data.raw_header = message[MESSAGE_HEADERS]
            self._preprocess_header()

        if message[MESSAGE_HTML] == "":
            response = self._get_html_and_har(self.website_data.url)
            message[MESSAGE_HTML] = response[MESSAGE_HTML]
            message[MESSAGE_HAR] = response[MESSAGE_HAR]
            if MESSAGE_HEADERS in message.keys():
                self.website_data.raw_header = response[MESSAGE_HEADERS]
                self._preprocess_header()

        if message[MESSAGE_HTML] != "" and self.website_data.html == "":
            self.website_data.html = message[MESSAGE_HTML].lower()
            self._create_html_soup()
            self._extract_images()
            self._extract_raw_links()
            self._extract_extensions()

        if message[MESSAGE_HAR] != "" and not self.website_data.har:
            self._load_har(message[MESSAGE_HAR])

    def _extract_top_level_domain(self) -> None:
        try:
            if self.tld_extractor is not None:
                self.website_data.top_level_domain = self.tld_extractor(
                    url=self.website_data.url
                ).domain
        except (ConnectionError, SuffixListNotFound, ValueError) as e:
            self._logger.error(
                f"Cannot extract top_level_domain because '{e.args}'"
            )
            self.website_data.top_level_domain = ""

    def _preprocess_header(self) -> None:
        header: str = self.website_data.raw_header.lower()

        header = (
            header.replace("b'", '"')
            .replace("/'", '"')
            .replace("'", '"')
            .replace('""', '"')
            .replace('/"', "/")
        )

        idx = header.find('b"')
        if idx >= 0 and header[idx - 1] == "[":
            bracket_idx = header[idx:].find("]")
            header = (
                header[:idx]
                + '"'
                + header[idx + 2 : idx + bracket_idx - 2].replace('"', " ")
                + header[idx + bracket_idx - 1 :]
            )
        self.website_data.headers = json.loads(header)

    @staticmethod
    def _transform_raw_header(raw_headers: list) -> dict:
        headers = {
            header_element["name"]: [header_element["value"].replace('"', "")]
            for header_element in raw_headers
        }
        return headers

    def _get_html_and_har(self, url: str) -> dict:
        splash_url = (
            f"{SPLASH_URL}/render.json?url={url}&html={1}&iframes={1}"
            f"&har={1}&response_body={1}&wait={1}"
        )
        try:
            response = requests.get(
                url=splash_url,
                headers=SPLASH_HEADERS,
                params={},
            )
            data = json.loads(response.content.decode("UTF-8"))
        except (JSONDecodeError, OSError) as e:
            self._logger.error(f"Error extracting data from splash: {e.args}")
            data = {}
        except Exception:
            raise ConnectionError

        try:
            raw_headers = data["har"]["log"]["entries"][0]["response"][
                "headers"
            ]
        except KeyError:
            raw_headers = []

        html = ""
        har = ""
        headers = ""
        try:
            html = data["html"]
            har = str(json.dumps(data["har"]))
            headers = str(json.dumps(self._transform_raw_header(raw_headers)))
        except KeyError as e:
            exception = (
                f"Key error from splash container data: '{e.args}'. "
                f"{''.join(traceback.format_exception(None, e, e.__traceback__))}"
            )
            self._logger.exception(
                exception,
                exc_info=True,
            )

        return {
            MESSAGE_HTML: html,
            MESSAGE_HAR: har,
            MESSAGE_HEADERS: headers,
        }

    def _create_html_soup(self) -> None:
        self.website_data.soup = BeautifulSoup(
            self.website_data.html, "html.parser"
        )

    @staticmethod
    def _get_unique_list(items: list) -> list:
        seen = set()
        for element in range(len(items) - 1, -1, -1):
            item = items[element]
            if item in seen:
                del items[element]
            else:
                seen.add(item)
        return items

    def _extract_raw_links(self) -> None:

        source_regex = self.source_regex.findall
        links = [
            link
            for tag in self.website_data.soup.find_all()
            for element in self.website_data.soup.find_all(tag.name)
            for link in self._get_raw_link_from_tag_element(
                element, source_regex, tag.name
            )
            if link is not None
        ]
        self.website_data.raw_links = self._get_unique_list(
            links
            + [el for el in self.website_data.image_links if el is not None]
        )

    @staticmethod
    def _get_raw_link_from_tag_element(
        element: bs4.element.ResultSet,
        source_regex,
        tag: BeautifulSoup,
    ) -> list:
        attributes = [
            "href",
            "src",
            "srcset",
            "img src",
            "data-src",
            "data-srcset",
        ]
        links = []
        if element is not None:
            if tag == "script":
                matches = source_regex(str(element).replace("\n", ""))
                if matches:
                    links += matches
            links += [
                element.attrs.get(attribute)
                for attribute in attributes
                if element.has_attr(attribute)
            ]
        return links

    def _extract_images(self) -> None:
        self.website_data.image_links = [
            image.attrs.get("src")
            for image in self.website_data.soup.findAll("img")
        ]

    def _extract_extensions(self) -> None:
        file_extensions = [
            os.path.splitext(urlparse(link)[2])[-1]
            for link in self.website_data.raw_links
        ]
        self.website_data.extensions = [
            x for x in self._get_unique_list(file_extensions) if x != ""
        ]

    def _load_har(self, har: str) -> None:
        self.website_data.har = json.loads(har.replace("\n", ""))

    def get_website_data_to_log(self) -> dict:
        data = {}
        data.update(
            {
                "raw_links": self.website_data.raw_links,
                "image_links": self.website_data.image_links,
                "extensions": self.website_data.extensions,
            }
        )

        return data

    def reset(self) -> None:
        """
        Since the manager works on many websites consecutively, the website manager needs to be reset.

        """
        self.website_data = WebsiteData()
