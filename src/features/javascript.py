from core.metadata_base import MetadataBase
from core.website_manager import WebsiteData


@MetadataBase.with_key()
class Javascript(MetadataBase):
    decision_threshold = 0

    def _start(self, website_data: WebsiteData) -> list[str]:
        matches = []
        for script in website_data.soup.select("script"):
            attributes = script.attrs
            if "src" in attributes.keys():
                matches.append(attributes["src"])

        return matches
