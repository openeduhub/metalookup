import re

from app.models import Explanation, StarCase
from core.metadata_base import MetadataBase
from core.website_manager import WebsiteData
from lib.constants import STRICT_TRANSPORT_SECURITY


@MetadataBase.with_key(key="g_d_p_r")  # fixme use GDPR as key!
class GDPR(MetadataBase):
    tag_list = ["impressum"]
    decision_threshold = 0.3

    @staticmethod
    def _check_https_in_url(website_data: WebsiteData) -> list[str]:
        value = "not" if "https" not in website_data.url else ""
        return [value + "https_in_url"]

    def _get_hsts(self, website_data: WebsiteData) -> list:
        if STRICT_TRANSPORT_SECURITY in website_data.headers.keys():
            sts = website_data.headers[STRICT_TRANSPORT_SECURITY]
            values = ["hsts"]
            values.extend(self._extract_sts(sts))
            values.extend(self._extract_max_age(sts))
        else:
            values = ["no_hsts"]
        return values

    @staticmethod
    def _extract_max_age(sts: list) -> list[str]:
        values = ["do_not_max_age"]
        regex = re.compile(r"max-age=(\d*)")
        try:
            match = min(
                [int(regex.match(element).group(1)) for element in sts]
            )
            if match > 10886400:
                values = ["max_age"]
        except AttributeError:
            pass
        return values

    @staticmethod
    def _extract_sts(sts: list) -> list[str]:
        values = []
        for key in ["includesubdomains", "preload"]:
            matches = [element for element in sts if key in element]
            if matches:
                values += [key]
            else:
                values += [f"do_not_{key}"]
        return values

    @staticmethod
    def _get_referrer_policy(website_data: WebsiteData) -> list[str]:
        referrer_policy = "referrer-policy"
        if referrer_policy in website_data.headers.keys():
            values = website_data.headers[referrer_policy]
        else:
            values = [f"no_{referrer_policy}"]

        regex = re.compile(r"<link rel=(.*?)href")
        matches = re.findall(regex, website_data.html.lower())
        if matches:
            values += [
                match.replace('"', "").replace(" ", "") for match in matches
            ]
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

    async def _start(self, website_data: WebsiteData) -> list[str]:
        values = await super()._start(website_data=website_data)

        for func in [
            self._check_https_in_url,
            self._get_hsts,
            self._get_referrer_policy,
            self._find_fonts,
            self._find_input_fields,
        ]:
            values += func(website_data=website_data)

        return list(set(values))

    def _decide(
        self, website_data: WebsiteData
    ) -> tuple[StarCase, list[Explanation]]:
        probability = 0.5

        if (
            "https_in_url" not in website_data.values
            or "hsts" not in website_data.values
            or "impressum" not in website_data.values
        ):
            probability = 0

        if "max_age" not in website_data.values:
            probability -= 0.1
        if "found_no_fonts" in website_data.values:
            probability -= 0.1

        decision = self._get_inverted_decision(max(probability, 0))
        if decision == StarCase.FIVE:
            decision = StarCase.ONE

        explanation = (
            [Explanation.MinimumGDPRRequirementsCovered]
            if decision == StarCase.ONE
            else [Explanation.PotentiallyInsufficientGDPRFound]
        )
        return decision, explanation
