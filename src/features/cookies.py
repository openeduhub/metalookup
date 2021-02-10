from features.metadata_base import MetadataBase
from features.website_manager import WebsiteData
from lib.constants import VALUES


class Cookies(MetadataBase):
    decision_threshold = 0.5

    def _start(self, website_data: WebsiteData) -> dict:
        try:
            data: list = website_data.har["log"]["entries"]
        except KeyError:
            data = []

        raw_cookies = [
            cookie
            for element in data
            for key in ("response", "request")
            for cookie in element[key]["cookies"]
        ]

        return {VALUES: raw_cookies}

    def _decide(self, website_data: WebsiteData) -> tuple[bool, float]:
        insecure_cookies = [
            cookie
            for cookie in website_data.values
            if not cookie["httpOnly"] or not cookie["secure"]
        ]

        probability = 1 if insecure_cookies else 0
        decision = probability > self.decision_threshold
        return decision, probability
