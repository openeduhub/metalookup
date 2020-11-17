from features.metadata_base import MetadataBase
from features.website_manager import WebsiteData
from lib.constants import VALUES


class Cookies(MetadataBase):
    def _start(self, website_data: WebsiteData) -> dict:
        cookies = []
        data: list = website_data.har["log"]["entries"]
        for element in data:
            cookies += element["response"]["cookies"]
            cookies += element["request"]["cookies"]
        cookies = [cookie for cookie in cookies if cookie]

        return {VALUES: cookies}
