from core.metadata_base import MetadataBase
from core.website_manager import WebsiteData
from lib.constants import VALUES


class Javascript(MetadataBase):
    decision_threshold = 0

    def _start(self, website_data: WebsiteData) -> dict:
        scripts = list(website_data.soup.select("script"))

        matches = []
        for script in scripts:
            attributes = script.attrs
            if "src" in attributes.keys():
                matches.append(attributes["src"])

        return {VALUES: matches}
