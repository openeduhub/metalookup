from features.metadata_base import MetadataBase
from features.website_manager import WebsiteData
from lib.constants import VALUES


class Accessibility(MetadataBase):
    tag_list = ["impressum"]

    def _start(self, website_data: WebsiteData) -> dict:
        return {VALUES: []}
