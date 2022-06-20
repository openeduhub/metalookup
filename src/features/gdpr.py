import re
from concurrent.futures import Executor

from app.models import Explanation, StarCase
from core.extractor import Extractor
from core.website_manager import WebsiteData

_MINIMUM_GDPR_REQUIREMENT_COVERED = "Minimum GDPR Requirements covered"
_POTENTIALLY_INSUFFICIENT_GDPR_REQUIREMENTS = "Potentially non GDPR compliant"


class GDPR(Extractor[set[str]]):
    key = "gdpr"
    tag_list = ["impressum"]
    decision_threshold = 0.3
    _MAX_AGE_REGEX = re.compile(r"max-age=(\d*)")
    _MAX_AGE_REQUIREMENT = 100 * 24 * 60 * 60  # 100 days

    async def setup(self):
        pass

    async def extract(self, site: WebsiteData, executor: Executor) -> tuple[StarCase, Explanation, set[str]]:
        html = site.html.lower()
        values = [ele for ele in self.tag_list if ele in html]

        for func in [
            self._check_https_in_url,
            self._get_hsts,
            self._get_referrer_policy,
            self._find_fonts,
            self._find_input_fields,
        ]:
            values += func(website_data=site)

        values = set(values)

        star_case, explanation = self.decide(values=values)
        return star_case, explanation, values

    def decide(self, values: set[str]) -> tuple[StarCase, Explanation]:
        probability = 0.5

        if "https_in_url" not in values or "hsts" not in values or "impressum" not in values:
            probability = 0

        if "max_age" not in values:
            probability -= 0.1
        if "found_no_fonts" in values:
            probability -= 0.1

        def _get_inverted_decision(probability: float) -> StarCase:
            decision = StarCase.ONE
            if probability > 0:
                if probability <= self.decision_threshold:
                    decision = StarCase.ZERO
                else:
                    decision = StarCase.FIVE
            return decision

        decision = _get_inverted_decision(max(probability, 0))
        if decision == StarCase.FIVE:
            decision = StarCase.ONE

        explanation = (
            _MINIMUM_GDPR_REQUIREMENT_COVERED
            if decision == StarCase.ONE
            else _POTENTIALLY_INSUFFICIENT_GDPR_REQUIREMENTS
        )
        return decision, explanation

    @staticmethod
    def _check_https_in_url(website_data: WebsiteData) -> list[str]:
        value = "not" if "https" not in website_data.url else ""
        return [value + "https_in_url"]

    def _get_hsts(self, website_data: WebsiteData) -> list:
        if "strict-transport-security" in website_data.headers.keys():
            sts = website_data.headers["strict-transport-security"]
            values = ["hsts"]
            values.extend(self._extract_sts(sts.split(";")))
            values.extend(self._extract_max_age(sts.split(";")))
        else:
            values = ["no_hsts"]
        return values

    @classmethod
    def _extract_max_age(cls, sts: list[str]) -> list[str]:
        for value in sts:
            if match := cls._MAX_AGE_REGEX.match(value):
                if int(match.group(1)) >= cls._MAX_AGE_REQUIREMENT:
                    return ["max_age"]
        return ["do_not_max_age"]

    @staticmethod
    def _extract_sts(sts: list[str]) -> list[str]:
        normalized = {e.lower().strip() for e in sts}
        return [key if key in normalized else f"do_not_{key}" for key in ["includesubdomains", "preload"]]

    @staticmethod
    def _get_referrer_policy(website_data: WebsiteData) -> list[str]:
        referrer_policy = "referrer-policy"
        if referrer_policy in website_data.headers.keys():
            values = [website_data.headers[referrer_policy]]
        else:
            values = [f"no_{referrer_policy}"]

        regex = re.compile(r"<link rel=(.*?)href")
        matches = re.findall(regex, website_data.html.lower())
        if matches:
            values += [match.replace('"', "").replace(" ", "") for match in matches]
        else:
            values += ["no_link_rel"]
        return values

    @staticmethod
    def _find_fonts(website_data: WebsiteData) -> list[str]:
        regex = re.compile(r"@font-face\s*{[\s\w\d\D\n]*?}")
        matches = re.findall(regex, website_data.html.lower())
        url_regex = re.compile(r"url\((.*?)\)")

        found_fonts = []
        for match in matches:
            found_fonts += list(re.findall(url_regex, match))

        if found_fonts:
            found_fonts = "found_fonts," + ",".join(found_fonts)
        else:
            found_fonts = "found_no_fonts"
        return [found_fonts]

    @staticmethod
    def _find_input_fields(website_data: WebsiteData) -> list[str]:
        inputs = []
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
        for input_type in input_types:
            matches = website_data.soup.find_all(input_type)
            if matches:
                inputs += [input_type]

        if inputs:
            inputs = "found_inputs," + ",".join(inputs)
        else:
            inputs = "found_no_inputs"
        return [inputs]
