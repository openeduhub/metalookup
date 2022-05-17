import http
import json
import os
import re
import time
from dataclasses import dataclass
from logging import Logger
from typing import Any, NoReturn
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from tldextract.tldextract import TLDExtract

from app.communication import Message
from lib.constants import SCRIPT
from lib.settings import SPLASH_HEADERS, SPLASH_TIMEOUT, SPLASH_URL
from lib.timing import global_start
from lib.tools import get_unique_list


@dataclass  # fixme: make frozen
class WebsiteData:
    url: str
    html: str
    raw_header: str
    soup: BeautifulSoup
    har: dict[str, Any]
    domain: str
    """A dictionary with the http headers where all keys have been converted to lowercase."""
    headers: dict[str, str]
    values: list[str]  # fixme: remove
    raw_links: list[str]
    image_links: list[str]
    extensions: list[str]

    @classmethod
    def fetch_content(
        cls, message: Message
    ) -> Message:  # fixme: make this async
        """
        Build a new message from url in given message where html content, headers and har are populated.

        Uses splash, so the splash docker container must be running an reachable.

        Will raise if splash is not reachable or the returned response is malformed (doesn't match expected structure).
        """

        splash_url = (
            f"{SPLASH_URL}/render.json?url={message.url}&html={1}&iframes={1}"
            f"&har={1}&response_body={1}&wait={10}&render_all={1}&script={1}&timeout={SPLASH_TIMEOUT}"
        )
        response = requests.get(
            url=splash_url,
            headers=SPLASH_HEADERS,
            params={},
        )
        data = json.loads(response.content.decode("UTF-8"))

        return Message(
            url=message.url,
            html=data["html"],
            header=data["har"]["log"]["entries"][0]["response"]["headers"],
            har=data["har"],
            extractors=message.extractors,
            bypass_cache=message.bypass_cache,
            _shared_memory_name=message._shared_memory_name,
        )

    @classmethod
    def from_message(
        cls, message: Message, tld_extractor: TLDExtract, logger: Logger
    ) -> "WebsiteData":
        def top_level_domain(url: str) -> str:
            host = tld_extractor(
                url=url.replace("http://", "").replace("https://", "")
            )
            domain = [host.subdomain, host.domain, host.suffix]
            return ".".join([element for element in domain if element != ""])

        def extract_raw_links(
            soup: BeautifulSoup, image_links: list[str]
        ) -> list[str]:
            source_regex = re.compile(
                r"src\=[\"|\']([\w\d\:\/\.\-\?\=]+)[\"|\']"
            )
            logger.debug("extracting raw links")
            unique_tags = get_unique_list(
                [tag.name for tag in soup.find_all()]
            )
            logger.debug(f"unique_tags: {unique_tags}")
            if SCRIPT in unique_tags:
                unique_tags.remove(SCRIPT)
                source_regex = source_regex.findall
                script_links = [
                    link
                    for element in soup.find_all(SCRIPT)
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
                for element in get_unique_list(soup.find_all(tag))
                for attribute in attributes
                if element.has_attr(attribute)
            ]
            logger.debug(
                f"Found links at {time.perf_counter() - global_start} since start: {len(links)}"
            )
            return get_unique_list(
                links
                + [el for el in image_links if el is not None]
                + script_links
            )

        def extract_extensions(raw_links: list[str]) -> list[str]:
            def extension_from_link(link: str):
                return os.path.splitext(urlparse(link)[2])[-1]

            file_extensions = [extension_from_link(link) for link in raw_links]
            return [x for x in get_unique_list(file_extensions) if x != ""]

        def preprocess_header(header: str) -> dict:
            header = header.lower()

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
                return json.loads(header)
            return {}

        fetched_from_splash = False
        if (
            message.html is None
            or message.header is None
            or message.har is None
        ):
            logger.debug(
                f"Missing one of html, header, or har -> fetching {message.url}"
            )
            message = cls.fetch_content(message)
            fetched_from_splash = True

        def headers_from_splash(
            headers: list[dict[str, str]]
        ) -> dict[str, str]:
            """
            Splash returns headers as a list of dicts with 'name' and 'value' entries for each header field.
            Here this list of dicts is transformed into a single dictionary with lowercase header field names.

            Note: If splash does not normalize duplicate header fields into a comma separate list, then we will lose
            them here!
            """
            return {d["name"].lower().strip(): d["value"] for d in headers}

        soup = BeautifulSoup(message.html, "lxml")
        image_links = [image.attrs.get("src") for image in soup.findAll("img")]
        raw_links = extract_raw_links(soup=soup, image_links=image_links)
        return WebsiteData(
            url=message.url,
            html=message.html,
            # fixme: remove the separate code paths
            raw_header=json.dumps(message.header)
            if fetched_from_splash
            else message.header,
            domain=top_level_domain(url=message.url),
            soup=soup,
            har=message.har,
            image_links=image_links,
            raw_links=raw_links,
            # fixme: remove the separate code paths
            headers=headers_from_splash(message.header)
            if fetched_from_splash
            else preprocess_header(message.header),
            extensions=extract_extensions(raw_links=raw_links),
            values=[],
        )


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
