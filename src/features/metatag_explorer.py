from app.models import Explanation, StarCase
from core.metadata_base import MetadataBase
from core.website_manager import WebsiteData


@MetadataBase.with_key()
class MetatagExplorer(MetadataBase):
    decision_threshold = 1

    async def _start(self, website_data: WebsiteData) -> list[str]:
        matches = []
        for tag in website_data.soup.select("meta"):
            if "name" in tag.attrs.keys() and "content" in tag.attrs.keys():
                matches += [tag.attrs["name"], tag.attrs["content"]]

        return matches

    def _decide(self, website_data: WebsiteData) -> tuple[StarCase, list[Explanation]]:
        decision = StarCase.ONE
        explanation = [Explanation.none]

        return decision, explanation
