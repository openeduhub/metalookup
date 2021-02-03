import re

from features.metadata_base import MetadataBase
from features.website_manager import WebsiteData
from lib.constants import VALUES


class GDPR(MetadataBase):
    tag_list = ["impressum"]
    decision_threshold = 0.9

    @staticmethod
    def _is_https_in_url(website_data: WebsiteData) -> tuple[list, list]:
        http = "http"
        https = "https"
        https_in_url = https in website_data.url
        if https_in_url:
            value = ["https_in_url"]
        else:
            value = ["https_not_in_url"]

        https_in_all_links = [
            True if https in url or http not in url else False
            for url in website_data.raw_links
        ]
        if False in https_in_all_links:
            http_links = website_data.raw_links[
                https_in_all_links.index(False)
            ]
        else:
            http_links = []
        return value, http_links

    @staticmethod
    def _has_hsts(website_data: WebsiteData) -> list:
        values = []
        strict_transport_security = "strict-transport-security"
        hsts = strict_transport_security in website_data.headers.keys()

        if hsts:
            values += ["hsts"]
            sts = website_data.headers[strict_transport_security]

            for key in ["includesubdomains", "preload"]:
                matches = [element for element in sts if key in element]
                if len(matches) > 0:
                    values += [key]
                else:
                    values += [f"do_not_{key}"]

            regex = re.compile(r"max-age=(\d*)")
            try:
                match = min(
                    [int(regex.match(element).group(1)) for element in sts]
                )
                if match > 10886400:
                    values += ["max_age"]
            except AttributeError:
                values += ["do_not_max_age"]
        else:
            values += ["no_hsts"]
        return values

    @staticmethod
    def _has_referrer_policy(website_data: WebsiteData) -> list:
        referrer_policy = "referrer-policy"
        rp = referrer_policy in website_data.headers.keys()
        if rp:
            values = [website_data.headers[referrer_policy]]
        else:
            values = [f"no_{referrer_policy}"]

        regex = re.compile(r"referrerpolicy")
        matches = re.findall(regex, website_data.html)

        if len(matches) > 0:
            values += [matches]
        else:
            values += ["no_referrerpolicy"]

        regex = re.compile(r"<link rel=(.*?)href")
        matches = re.findall(regex, website_data.html)

        if len(matches) > 0:
            values += [
                match.replace('"', "").replace(" ", "") for match in matches
            ]
        else:
            values += ["no_link_rel"]

        return values

    @staticmethod
    def _find_fonts(website_data: WebsiteData) -> list:
        regex = re.compile(r"@font-face\s*{[\s\w\d\D\n]*?}")
        matches = re.findall(regex, website_data.html)
        url_regex = re.compile(r"url\((.*?)\)")

        found_fonts = []
        for match in matches:
            url_matches = re.findall(url_regex, match)
            for url_match in url_matches:
                found_fonts.append(url_match)

        if len(found_fonts) > 0:
            found_fonts = "found_fonts," + ",".join(found_fonts)
        else:
            found_fonts = "found_no_fonts"
        return [found_fonts]

    @staticmethod
    def _find_input_fields(website_data: WebsiteData) -> list:
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
            if len(matches) > 0:
                inputs += [input_type]

        if len(inputs) > 0:
            inputs = "found_inputs," + ",".join(inputs)
        else:
            inputs = "found_no_inputs"
        return [inputs]

    def _start(self, website_data: WebsiteData) -> dict:
        impressum = super()._start(website_data=website_data)[VALUES]
        values = impressum

        value, http_links = self._is_https_in_url(website_data=website_data)
        values += value

        values += self._has_hsts(website_data=website_data)

        values += self._has_referrer_policy(website_data=website_data)

        values += self._find_fonts(website_data=website_data)

        values += self._find_input_fields(website_data=website_data)

        flat_values = []
        for value in values:
            if isinstance(value, list):
                for el in value:
                    flat_values.append(el)
            else:
                flat_values.append(value)

        return {VALUES: list(set(flat_values)), "http_links": http_links}

    def _decide(self, website_data: WebsiteData) -> tuple[bool, float]:
        decision_indicator = 0.5

        if (
            "https_in_url" not in website_data.values
            or "hsts" not in website_data.values
            or "impressum" not in website_data.values
        ):
            decision_indicator = 0
        elif (
            "max_age" not in website_data.values
            or "found_no_fonts" in website_data.values
            or "found_no_inputs" in website_data.values
        ):
            decision_indicator -= 0.1

        if decision_indicator < 0:
            decision_indicator = 0

        decision = decision_indicator > self.decision_threshold
        return decision, decision_indicator
