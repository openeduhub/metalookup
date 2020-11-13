import json
import os
from dataclasses import dataclass, field
from typing import Optional

from bs4 import BeautifulSoup
from tldextract import tldextract


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
    top_level_domain: Optional[tldextract.TLD_EXTRACTOR] = None


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

    def __init__(self):
        super().__init__()

        self.website_data = WebsiteData()

    def load_raw_data(
        self,
        url: str = "",
        html_content: str = "",
        raw_header: str = "",
        headers: dict = None,
    ) -> None:
        if headers is None:
            headers = {}

        if self.website_data.headers == {}:
            self.website_data.headers = headers

        if self.website_data.url == "":
            self.website_data.url = url
            self._extract_host_name()

        if self.website_data.raw_header == "":
            self.website_data.raw_header = raw_header

        if raw_header != "":
            self._preprocess_header()

        if html_content != "" and self.website_data.html == "":
            self.website_data.html = html_content
            self._create_html_soup()
            self._extract_raw_links()
            self._extract_images()
            self._extract_extensions()

    def _extract_host_name(self):
        self.website_data.top_level_domain = tldextract.extract(
            self.website_data.url
        ).domain

    def _create_html_soup(self):
        self.website_data.soup = BeautifulSoup(
            self.website_data.html, "html.parser"
        )

    def _extract_raw_links(self):
        self.website_data.raw_links = list(
            {a["href"] for a in self.website_data.soup.find_all(href=True)}
        )

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

    def _preprocess_header(self) -> None:
        header: str = self.website_data.raw_header
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
