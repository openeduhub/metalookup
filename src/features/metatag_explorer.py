from app.models import Explanation, StarCase
from core.metadata_base import MetadataBase
from core.website_manager import WebsiteData
from lib.constants import VALUES


class MetatagExplorer(MetadataBase):
    decision_threshold = 1

    def _start(self, website_data: WebsiteData) -> dict:
        metatags = list(website_data.soup.select("meta"))

        matches = []
        for tag in metatags:
            if "name" in tag.attrs.keys() and "content" in tag.attrs.keys():
                matches.append([tag.attrs["name"], tag.attrs["content"]])

        return {VALUES: matches}

    def _decide(
        self, website_data: WebsiteData
    ) -> tuple[StarCase, list[Explanation]]:
        decision = StarCase.ONE
        explanation = [Explanation.none]

        return decision, explanation
