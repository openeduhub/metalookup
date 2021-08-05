from app.models import DecisionCase, Explanation
from features.metadata_base import ExtractionMethod, MetadataBase
from features.website_manager import WebsiteData
from lib.constants import VALUES


class Cookies(MetadataBase):
    decision_threshold = 0.5
    urls = [
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_general_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_general_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_international_specific_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_international_specific_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_specific_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_specific_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_thirdparty.txt",
    ]
    call_async = False
    extraction_method = ExtractionMethod.USE_ADBLOCK_PARSER

    def _start(self, website_data: WebsiteData) -> dict:
        values = super()._start(website_data=website_data)[VALUES]

        try:
            data: list = website_data.har["log"]["entries"]
        except KeyError as e:
            data = []

        raw_cookies = [
            cookie
            for element in data
            for key in ("response", "request")
            for cookie in element[key]["cookies"]
        ]

        return {VALUES: raw_cookies + values}

    def _decide(
        self, website_data: WebsiteData
    ) -> tuple[DecisionCase, float, list[Explanation]]:
        cookies_in_html = [
            cookie for cookie in website_data.values if isinstance(cookie, str)
        ]

        insecure_cookies = [
            cookie
            for cookie in website_data.values
            if not isinstance(cookie, str)
            and (not cookie["httpOnly"] or not cookie["secure"])
        ]

        probability = 1 if insecure_cookies or cookies_in_html else 0
        decision = self._get_decision(probability)
        explanation = (
            [Explanation.CookiesFound]
            if decision == DecisionCase.TRUE
            else [Explanation.NoCookiesFound]
        )
        return decision, probability, explanation
