from concurrent.futures import Executor

from app.models import Explanation, StarCase
from app.splash_models import Cookie, Entry
from core.extractor import ExtractionMethod, MetadataBase
from core.website_manager import WebsiteData

_COOKIES_FOUND = "Found Cookies"
_NO_COOKIES_FOUND = "Found no Cookies"


# fixme: we still need the MetadataBase inheritance for now, as it contains the setup code for the tag lists
@MetadataBase.with_key()
class Cookies(MetadataBase):
    """
    The returned extra data is a list of strings with the detected critical cookie names.
    """

    urls = [
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_general_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_general_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_international_specific_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_international_specific_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_specific_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_specific_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_thirdparty.txt",
    ]

    # fixme: still needed because it modifies the setup call...
    extraction_method = ExtractionMethod.USE_ADBLOCK_PARSER

    async def extract(self, site: WebsiteData, executor: Executor) -> tuple[StarCase, Explanation, list[str]]:
        entries: list[Entry] = site.har.log.entries

        cookies_in_html = self._parse_adblock_rules(website_data=site)

        insecure_cookies: list[Cookie] = [
            cookie
            for entry in entries
            for cookies in (entry.response.cookies, entry.request.cookies)
            for cookie in cookies
        ]

        stars = StarCase.ZERO if insecure_cookies or cookies_in_html else StarCase.FIVE
        explanation = _COOKIES_FOUND if stars == StarCase.ZERO else _NO_COOKIES_FOUND
        extra = cookies_in_html + [f"{c.name}={c.value}" for c in insecure_cookies]
        return stars, explanation, extra
