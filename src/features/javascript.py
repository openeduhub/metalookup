import os
import re

from bs4 import BeautifulSoup, element

from features.metadata_base import MetadataBase
from features.website_manager import WebsiteData
from lib.constants import VALUES


class Javascript(MetadataBase):
    def _start(self, website_data: WebsiteData) -> dict:
        scripts = list(website_data.soup.select("script"))

        matches = []
        for script in scripts:
            attributes = script.attrs
            if "src" in attributes.keys():
                matches.append(attributes["src"])

        return {VALUES: matches}
