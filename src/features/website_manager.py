import json
import os
import re
import time
import traceback
from dataclasses import dataclass, field
from json import JSONDecodeError
from typing import NoReturn, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from tldextract.suffix_list import SuffixListNotFound
from tldextract.tldextract import TLDExtract

from lib.constants import (
    MESSAGE_HAR,
    MESSAGE_HEADERS,
    MESSAGE_HTML,
    MESSAGE_URL,
    SCRIPT,
)
from lib.logger import get_logger
from lib.settings import SPLASH_HEADERS, SPLASH_TIMEOUT, SPLASH_URL
from lib.timing import global_start
from lib.tools import get_unique_list


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
    domain: str = field(default_factory=str)
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
        self._logger = get_logger()

        try:
            self.tld_extractor: Optional[TLDExtract] = TLDExtract(
                cache_dir=False
            )
        except (ConnectionError, SuffixListNotFound) as e:
            self._logger.error(
                f"Cannot extract top_level_domain because '{e.args}'"
            )
            self.tld_extractor = None

        self.reset()

    def load_website_data(self, message: dict = None) -> None:
        if message is None:
            return

        if self.website_data.url == "":
            self.website_data.url = message[MESSAGE_URL]
            self._extract_top_level_domain()

        if message[MESSAGE_HTML] == "":
            response = self._get_html_and_har(self.website_data.url)
            message[MESSAGE_HTML] = response[MESSAGE_HTML]
            message[MESSAGE_HAR] = response[MESSAGE_HAR]
            message[MESSAGE_HEADERS] = response[MESSAGE_HEADERS]

        if message[MESSAGE_HEADERS] != "":
            self.website_data.raw_header = message[MESSAGE_HEADERS]
            self._preprocess_header()

        if message[MESSAGE_HTML] != "":
            self.website_data.html = message[MESSAGE_HTML]
            self._create_html_soup()
            self._extract_images()
            self._extract_raw_links()
            self._extract_extensions()

        if message[MESSAGE_HAR] != "":
            self._load_har(message[MESSAGE_HAR])

    def _extract_top_level_domain(self) -> None:
        try:
            if self.tld_extractor is not None:
                host = self.tld_extractor(
                    url=self.website_data.url.replace("http://", "").replace(
                        "https://", ""
                    )
                )
                domain = [host.subdomain, host.domain, host.suffix]
                self.website_data.domain = ".".join(
                    [element for element in domain if element != ""]
                )
        except (ConnectionError, SuffixListNotFound, ValueError) as e:
            self._logger.error(
                f"Cannot extract top_level_domain because '{e.args}'"
            )
            self.website_data.domain = ""

    def _preprocess_header(self) -> None:
        header: str = self.website_data.raw_header.lower()

        idx = max(header.find('b"'), header.find("b'"))
        if idx >= 0:
            header = (
                header.replace("b'", '"')
                .replace('b"', '"')
                .replace("/'", '"')
                .replace("'", '"')
                .replace('""', '"')
                .replace('/"', "/")
            )

        if len(header) > 0:
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
            f"&har={1}&response_body={1}&wait={10}&render_all={1}&script={1}&timeout={SPLASH_TIMEOUT}"
        )
        try:
            response = requests.get(
                url=splash_url,
                headers=SPLASH_HEADERS,
                params={},
            )
            data = json.loads(response.content.decode("UTF-8"))
        except (JSONDecodeError, OSError) as err:
            exception = (
                "Error extracting data from splash: "
                + str(err.args)
                + "".join(
                    traceback.format_exception(None, err, err.__traceback__)
                )
            )
            self._logger.error(exception)
            data = {}
        except Exception as err:
            raise ConnectionError from err

        try:
            raw_headers = data["har"]["log"]["entries"][0]["response"][
                "headers"
            ]
        except (KeyError, IndexError):
            raw_headers = []

        try:
            html = data["html"]
            har = str(json.dumps(data["har"]))
            headers = str(json.dumps(self._transform_raw_header(raw_headers)))
        except KeyError as e:
            exception = (
                f"Key error caught from splash container data: '{e.args}'. "
                "".join(traceback.format_exception(None, e, e.__traceback__))
                + f"\n Continuing with empty html. Data keys: {data.keys()}"
                + f"\nerror: {data['error'] if 'error' in data.keys() else ''}"
                + f"\ndescription: {data['description'] if 'description' in data.keys() else ''}"
                + f"\ninfo: {data['info'] if 'info' in data.keys() else ''}"
            )
            self._logger.exception(
                exception,
                exc_info=True,
            )
            html = ""
            har = ""
            headers = ""

        return {
            MESSAGE_HTML: html,
            MESSAGE_HAR: har,
            MESSAGE_HEADERS: headers,
        }

    def _create_html_soup(self) -> None:
        self.website_data.soup = BeautifulSoup(self.website_data.html, "lxml")

    def _extract_raw_links(self) -> None:
        self._logger.debug(
            f"_extract_raw_links starts at {time.perf_counter() - global_start} since start"
        )
        unique_tags = get_unique_list(
            [tag.name for tag in self.website_data.soup.find_all()]
        )
        self._logger.debug(f"unique_tags: {unique_tags}")
        if SCRIPT in unique_tags:
            unique_tags.remove(SCRIPT)
            source_regex = self.source_regex.findall
            script_links = [
                link
                for element in self.website_data.soup.find_all(SCRIPT)
                for link in source_regex(str(element).replace("\n", ""))
                if link
            ]
        else:
            script_links = []

        attributes = [
            "href",
            "src",
            "srcset",
            "img src",
            "data-src",
            "data-srcset",
        ]
        links = [
            element.attrs.get(attribute)
            for tag in unique_tags
            for element in get_unique_list(
                self.website_data.soup.find_all(tag)
            )
            for attribute in attributes
            if element.has_attr(attribute)
        ]
        self._logger.debug(
            f"Found links at {time.perf_counter() - global_start} since start: {len(links)}"
        )
        self.website_data.raw_links = get_unique_list(
            links
            + [el for el in self.website_data.image_links if el is not None]
            + script_links
        )

    def _extract_images(self) -> None:
        self.website_data.image_links = [
            image.attrs.get("src")
            for image in self.website_data.soup.findAll("img")
        ]

    def _get_extension_from_link(self, link: str):
        try:
            output = os.path.splitext(urlparse(link)[2])[-1]
        except ValueError as err:
            self._logger.exception(
                f"Could not parse file extension from link {link}. Exception: {err.args}"
            )
            output = ""
        return output

    def _extract_extensions(self) -> None:
        file_extensions = [
            self._get_extension_from_link(link)
            for link in self.website_data.raw_links
        ]
        self.website_data.extensions = [
            x for x in get_unique_list(file_extensions) if x != ""
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
        Since the manager works on many websites consecutively,
        the website manager needs to be reset.

        """
        self.website_data = WebsiteData()
