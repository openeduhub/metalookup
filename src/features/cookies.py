from app.models import Explanation, StarCase
from app.splash_models import Cookie, Entry
from core.extractor import ExtractionMethod, MetadataBase
from core.website_manager import WebsiteData

_COOKIES_FOUND = "Found Cookies"
_NO_COOKIES_FOUND = "Found no Cookies"


@MetadataBase.with_key()
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
    extraction_method = ExtractionMethod.USE_ADBLOCK_PARSER

    async def _start(self, website_data: WebsiteData) -> list[str]:
        values = await super()._start(website_data=website_data)

        entries: list[Entry] = website_data.har.log.entries

        raw_cookies = [
            cookie
            for entry in entries
            for cookies in (entry.response.cookies, entry.request.cookies)
            for cookie in cookies
        ]

        return raw_cookies + values

    def _decide(self, website_data: WebsiteData) -> tuple[StarCase, Explanation]:
        cookies_in_html = [cookie for cookie in website_data.values if isinstance(cookie, str)]

        insecure_cookies = [
            cookie
            for cookie in website_data.values
            if isinstance(cookie, Cookie) and (not cookie.httpOnly or not cookie.secure)
        ]

        probability = 1 if insecure_cookies or cookies_in_html else 0
        decision = self._get_decision(probability)
        explanation = _COOKIES_FOUND if decision == StarCase.ZERO else _NO_COOKIES_FOUND
        return decision, explanation
