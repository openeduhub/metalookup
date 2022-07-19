import re
from concurrent.futures import Executor
from typing import Optional

from pydantic import BaseModel

from metalookup.app.models import Explanation, StarCase
from metalookup.core.extractor import Extractor
from metalookup.core.website_manager import WebsiteData

_MINIMUM_GDPR_REQUIREMENT_COVERED = "Minimum GDPR Requirements covered"
_POTENTIALLY_INSUFFICIENT_GDPR_REQUIREMENTS = "Potentially non GDPR compliant"


class GDPRExtra(BaseModel):
    """
    Key features resulting in the GDPR rating.
    """

    has_legal_notice: bool
    is_https: bool
    strict_transport_security_expiry: Optional[int]
    """The value of the `strict-transport-security` header's max age directive (if present)."""
    referrer_policy: Optional[str]
    """The value of the `referrer-policy` header (if present)."""
    external_resources: list[str]
    """The list of links to external resources detected via the following pattern: `<link rel=(.*) hreg=(.*)>`."""
    fonts: list[str]
    """The list of detected fonts."""
    inputs: list[str]
    """The list of detected input form fields."""


class GDPR(Extractor[GDPRExtra]):
    key = "gdpr"
    decision_threshold = 0.3
    _MAX_AGE_REGEX = re.compile(r"max-age=(\d*);?.*")
    _MAX_AGE_REQUIREMENT = 100 * 24 * 60 * 60  # 100 days

    async def setup(self):
        pass

    async def extract(self, site: WebsiteData, executor: Executor) -> tuple[StarCase, Explanation, GDPRExtra]:
        extra = GDPRExtra(
            # this would only work for websites with german content. See e.g.
            # https://allcodesarebeautiful.com/impressum-auf-englisch-imprint-falsche-uebersetzung/
            # for a discussion about legal notice in other countries and why "imprint" is a wrong translation.
            has_legal_notice="impressum" in site.html.lower(),
            is_https=site.url.startswith("https"),
            strict_transport_security_expiry=self.strict_transport_security_expiry(site=site),
            referrer_policy=site.headers.get("referrer-policy"),
            external_resources=self.external_resources(site=site),
            fonts=self.fonts(site=site),
            inputs=self.input_fields(site=site),
        )

        star_case, explanation = self.decide(values=extra)
        return star_case, explanation, extra

    def decide(self, values: GDPRExtra) -> tuple[StarCase, Explanation]:
        no_https = not values.is_https
        no_legal_notice = not values.has_legal_notice
        no_strict_transport_security = values.strict_transport_security_expiry is None

        if no_https or no_legal_notice or no_strict_transport_security:
            score = 0
        else:
            score = 0.5

        if (
            values.strict_transport_security_expiry
            and values.strict_transport_security_expiry < self._MAX_AGE_REQUIREMENT
        ):
            score -= 0.1
        if len(values.fonts) == 0:
            score -= 0.1

        decision = StarCase.ONE
        if score > 0:
            if score <= self.decision_threshold:
                decision = StarCase.ZERO

        explanation = (
            _MINIMUM_GDPR_REQUIREMENT_COVERED
            if decision == StarCase.ONE
            else _POTENTIALLY_INSUFFICIENT_GDPR_REQUIREMENTS
        )
        return decision, explanation

    def strict_transport_security_expiry(self, site: WebsiteData) -> Optional[int]:
        if "strict-transport-security" in site.headers.keys():
            value = site.headers["strict-transport-security"]
            if match := self._MAX_AGE_REGEX.match(value):
                return int(match.group(1))

    @staticmethod
    def external_resources(site: WebsiteData) -> list[str]:
        regex = re.compile(r"<link rel=(.*?)href")
        if matches := re.findall(regex, site.html.lower()):
            return [match.replace('"', "").replace(" ", "") for match in matches]

        return []

    @staticmethod
    def fonts(site: WebsiteData) -> list[str]:
        regex = re.compile(r"@font-face\s*{[\s\w\d\D\n]*?}")
        url_regex = re.compile(r"url\((.*?)\)")

        found_fonts = []
        for match in re.findall(regex, site.html.lower()):
            found_fonts += list(re.findall(url_regex, match))

        return found_fonts

    @staticmethod
    def input_fields(site: WebsiteData) -> list[str]:
        input_types = [
            "input",
            "button",
            "checkbox",
            "color",
            "date",
            "datetime-local",
            "email",
            "file",
            "hidden",
            "image",
            "month",
            "number",
            "password",
            "radio",
            "range",
            "reset",
            "search",
            "submit",
            "tel",
            "text",
            "time",
            "url",
            "week",
            "datetime",
        ]
        inputs = []
        for input_type in input_types:
            if site.soup.find_all(input_type):
                inputs += [input_type]

        return inputs
