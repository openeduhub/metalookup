from features.metadata_base import MetadataBase
from features.website_manager import WebsiteData
from lib.constants import VALUES


class Cookies(MetadataBase):
    def _start(self, website_data: WebsiteData) -> dict:
        raw_cookies = []
        data: list = website_data.har["log"]["entries"]
        for element in data:
            raw_cookies += element["response"]["cookies"]
            raw_cookies += element["request"]["cookies"]
        raw_cookies = [cookie for cookie in raw_cookies if cookie]


        cookies = []

        for cookie in raw_cookies:
            name = cookie["name"]
            httpOnly = cookie["httpOnly"]
            secure = cookie["secure"]
            secure = cookie["secure"]
            domain = cookie["domain"]
            path = cookie["path"]
            expires = cookie["expires"]
        return {VALUES: cookies}
