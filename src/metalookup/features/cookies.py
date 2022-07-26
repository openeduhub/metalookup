import asyncio
from concurrent.futures import Executor

from metalookup.app.models import Explanation, StarCase
from metalookup.app.splash_models import Cookie, Entry
from metalookup.core.content import Content
from metalookup.features.adblock_based import AdBlockBasedExtractor

_COOKIES_FOUND = "Found potentially insecure Cookies"
_NO_COOKIES_FOUND = "Found no potentially insecure Cookies"


class Cookies(AdBlockBasedExtractor):
    """
    The returned extra data is a set of potentially malicious cookie names.
    """

    key = "cookies"

    urls = [
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_general_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_general_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_international_specific_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_international_specific_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_specific_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_specific_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_thirdparty.txt",
    ]

    async def extract(self, content: Content, executor: Executor) -> tuple[StarCase, Explanation, set[str]]:
        # Note: we derive from AdBlockBasedExtractor, but fully reimplement the extract function, as we don't want
        #       to apply the ad-block rules on links, but the detected cookies instead.
        entries: list[Entry] = (await content.har()).log.entries

        insecure_cookies: list[Cookie] = [
            cookie
            for entry in entries
            for cookies in (entry.response.cookies, entry.request.cookies)
            for cookie in cookies
            if not cookie.secure or not cookie.httpOnly
        ]

        loop = asyncio.get_running_loop()

        # validate the detected insecure cookies against the above adblock rules.
        duration, matches = await loop.run_in_executor(
            executor, self.apply_rules, await content.domain(), [cookie.name for cookie in insecure_cookies]
        )
        self.logger.info(f"Found {len(matches)} potentially malicious cookies in {duration:5.2}s")

        found_match = len(matches) > 0
        stars = StarCase.ZERO if found_match else StarCase.FIVE
        explanation = _COOKIES_FOUND if stars == StarCase.ZERO else _NO_COOKIES_FOUND
        return stars, explanation, matches
