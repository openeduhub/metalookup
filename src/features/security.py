from concurrent.futures import Executor
from typing import Callable

from app.models import Explanation, StarCase
from core.extractor import Extractor
from core.website_manager import WebsiteData

_MINIMUM_SECURITY_REQUIREMENTS_COVERED = "Minimum security requirements covered"
_INDICATORS_FOR_INSUFFICIENT_SECURITY_FOUND = "Indicators for insufficient security found"


class Security(Extractor[set[str]]):
    """
    Checks various HTTP headers for security aspects resulting in either a zero or five star rating.
    See '../../docs/acceptance.md#(Sicherheit alias Security)' for details.

    The returned extra data is a set of strings naming the http headers where the checks have failed.
    """

    key = "security"

    # The validators that all must yield a positive result for a website to get 5 stars.
    # If a header is not present, the validation result for the header defaults to false.
    # As headers field names are case insensitive (RFC 2616) hence only lower case is used here.
    header_checks: dict[str, Callable[[str], bool]] = {
        "content-security-policy": lambda _: True,
        "referrer-policy": lambda _: True,
        "cache-control": lambda s: "no-cache" in s.lower() or "no-store" in s.lower(),
        "x-content-type-options": lambda s: s.lower() == "nosniff",
        "x-frame-options": lambda s: s.lower() == "deny" or s.lower() == "sameorigin",
        "x-xss-protection": lambda s: "1;mode=block" in s.lower(),
        "strict-transport-security": lambda s: "includesubdomains" in s.lower(),
    }

    async def setup(self):
        pass

    async def extract(self, site: WebsiteData, executor: Executor) -> tuple[StarCase, Explanation, set[str]]:
        # No need to dispatch to the executor as this is a rather trivial computation
        passed_checks = [
            field for field, check in self.header_checks.items() if field in site.headers and check(site.headers[field])
        ]
        failed_checks = set(self.header_checks.keys()) - set(passed_checks)

        return (
            (StarCase.FIVE, _MINIMUM_SECURITY_REQUIREMENTS_COVERED, failed_checks)
            if len(passed_checks) == len(self.header_checks)
            else (StarCase.ZERO, _INDICATORS_FOR_INSUFFICIENT_SECURITY_FOUND, failed_checks)
        )
