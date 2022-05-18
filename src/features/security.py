from typing import Callable

from app.models import Explanation, StarCase
from core.metadata_base import MetadataBase
from core.website_manager import WebsiteData


@MetadataBase.with_key()
class Security(MetadataBase):
    """
    Checks various HTTP headers for security aspects resulting in either a zero or five star rating.
    See '../../docs/acceptance.md#(Sicherheit alias Security)' for details.
    """

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

    async def _start(self, website_data: WebsiteData) -> list[str]:
        """
        Run the header checks against the headers of given
        site and return the field names of the checks that passed.
        """
        return [
            field
            for field, check in self.header_checks.items()
            if field in website_data.headers and check(website_data.headers[field])
        ]

    def _decide(self, website_data: WebsiteData) -> tuple[StarCase, list[Explanation]]:
        # fixme: Currently copy pasted from _start.
        passed = [
            field
            for field, check in self.header_checks.items()
            if field in website_data.headers and check(website_data.headers[field])
        ]

        return (
            (StarCase.FIVE, [Explanation.MinimumSecurityRequirementsCovered])
            if len(passed) == len(self.header_checks)
            else (
                StarCase.ZERO,
                [Explanation.IndicatorsForInsufficientSecurityFound],
            )
        )
