import json
import os
import re
from dataclasses import dataclass, field

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
    cookies: list = field(default_factory=list)


class Singleton:
    _instance = None

    def __init__(self, cls):
        self._class = cls

    def get_instance(self):
        if self._instance is None:
            self._instance = self._class()
        return self._instance

    def __call__(self):
        raise TypeError(
            "Singletons must only be accessed through `get_instance()`."
        )

    def __instancecheck__(self, inst):
        return isinstance(inst, self._class)


@Singleton
class WebsiteManager:
    website_data: WebsiteData

    SPLASH_URL = "http://splash:8050"
    SPLASH_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36"
    }

    def __init__(self):
        super().__init__()

        self.website_data = WebsiteData()

    def load_raw_data(self, message: dict = None) -> None:
        if message is None:
            message = {}

        if self.website_data.url == "":
            self.website_data.url = message[MESSAGE_URL]
            self._extract_host_name()

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

        if message[MESSAGE_HTML] != "" and self.website_data.html == "":
            self.website_data.html = message[MESSAGE_HTML].lower()
            self._create_html_soup()
            self._extract_images()
            self._extract_raw_links()
            self._extract_extensions()

        if message[MESSAGE_HAR] != "" and not self.website_data.har:
            self._load_har(message[MESSAGE_HAR])

    def _extract_host_name(self):
        try:
            extractor = TLDExtract(cache_dir=False)
            self.website_data.top_level_domain = extractor(
                url=self.website_data.url
            ).domain
        except (ConnectionError, SuffixListNotFound, ValueError) as e:
            print(f"Cannot extract host name because '{e.args}'")
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

        header = json.loads(header)
        self.website_data.headers = header

    def _get_html_and_har(self, url):
        splash_url = (
            f"{self.SPLASH_URL}/render.json?url={url}&html={1}&iframes={1}"
            f"&har={1}&response_body={1}&wait={1}"
        )

        response = requests.get(
            url=splash_url, headers=self.SPLASH_HEADERS, params={}
        )

        data = json.loads(response.content.decode("UTF-8"))
        try:
            html = data["html"]
            har = str(json.dumps(data["har"]))
        except KeyError:
            html = ""
            har = ""

        return {
            MESSAGE_HTML: html,
            MESSAGE_HAR: har,
        }

    def _create_html_soup(self):
        self.website_data.soup = BeautifulSoup(
            self.website_data.html, "html.parser"
        )

    def _extract_raw_links(self):
        tags = {tag.name for tag in self.website_data.soup.find_all()}
        attributes = [
            "href",
            "src",
            "srcset",
            "img src",
            "data-src",
            "data-srcset",
        ]

        links = []
        for tag in tags:
            for el in self.website_data.soup.find_all(tag):
                if el is not None:
                    links += [
                        el.attrs.get(attribute)
                        for attribute in attributes
                        if el.has_attr(attribute)
                    ]

        self.website_data.raw_links = [
            el
            for el in list(set(links + self.website_data.image_links))
            if el is not None
        ]

    def _extract_images(self) -> None:
        self.website_data.image_links = [
            image.attrs.get("src")
            for image in self.website_data.soup.findAll("img")
        ]

    def _extract_extensions(self):
        file_extensions = [
            os.path.splitext(link)[-1]
            for link in self.website_data.image_links
        ]
        self.website_data.extensions = [
            x for x in list(set(file_extensions)) if x != ""
        ]

    def _load_har(self, har: str) -> None:
        self.website_data.har = json.loads(har)

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
