import json
import os
import re
import time
from dataclasses import dataclass
from logging import Logger
from typing import NoReturn
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from tldextract.tldextract import TLDExtract

from app.communication import Message
from app.splash_models import HAR, SplashResponse
from lib.constants import SCRIPT
from lib.settings import SPLASH_HEADERS, SPLASH_TIMEOUT, SPLASH_URL
from lib.timing import global_start
from lib.tools import get_unique_list


@dataclass  # fixme: make frozen
class WebsiteData:
    url: str
    html: str
    soup: BeautifulSoup
    har: HAR
    domain: str
    """A dictionary with the http headers where all keys have been converted to lowercase."""
    headers: dict[str, str]
    values: list[str]  # fixme: remove
    raw_links: list[str]
    image_links: list[str]
    extensions: list[str]

    # fixme: make this async
    @classmethod
    def fetch_content(cls, url: str) -> SplashResponse:
        """
        Build a new message from url in given message where html content, headers and har are populated.
        Uses splash, so the splash docker container must be running an reachable.
        Will raise if splash is not reachable or the returned response is malformed (doesn't match expected structure).
        """

        splash_url = (
            f"{SPLASH_URL}/render.json?url={url}&html={1}&iframes={1}"
            f"&har={1}&response_body={1}&wait={10}&render_all={1}&script={1}&timeout={SPLASH_TIMEOUT}"
        )
        response = requests.get(
            url=splash_url,
            headers=SPLASH_HEADERS,
            params={},
        )
        return SplashResponse.parse_obj(
            json.loads(response.content.decode("UTF-8"))
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

        if message.splash_response is None:
            logger.debug(f"Missing har -> fetching {message.url}")
            splash_response = cls.fetch_content(message.url)
        else:
            splash_response = message.splash_response

        def headers_from_splash(splash: SplashResponse) -> dict[str, str]:
            """
            Splash returns headers as a list of dicts with 'name' and 'value' entries for each header field.
            Here this list of dicts is transformed into a single dictionary with lowercase header field names.

            Note: As splash potentially does not normalize duplicate header fields into a comma separate list, we will
                  normalize them here!
            """
            result = dict()
            # fixme: we just use the first response here which might just be a redirect...
            #        See also https://github.com/openeduhub/metalookup/issues/85
            for header in splash.har.log.entries[0].response.headers:
                lower = header.name.lower()
                if lower not in result:
                    result[lower] = header.value
                else:
                    if result[lower].endswith(";"):
                        result[lower] = result[lower] + header.value
                    else:
                        result[lower] = result[lower] + ";" + header.value
            return result

        soup = BeautifulSoup(splash_response.html, "lxml")
        image_links = [image.attrs.get("src") for image in soup.findAll("img")]
        raw_links = extract_raw_links(soup=soup, image_links=image_links)

        return WebsiteData(
            url=message.url,
            html=splash_response.html,
            domain=top_level_domain(url=message.url),
            soup=soup,
            har=splash_response.har,
            image_links=image_links,
            raw_links=raw_links,
            headers=headers_from_splash(splash_response),
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
