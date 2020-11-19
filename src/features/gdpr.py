import re

from features.metadata_base import MetadataBase
from features.website_manager import WebsiteData
from lib.constants import VALUES


class GDPR(MetadataBase):
    tag_list = ["impressum"]

    def _https_in_url(self, website_data: WebsiteData) -> tuple[list, list]:
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
        http_links = website_data.raw_links[https_in_all_links.index(False)]
        return value, http_links

    def _hsts(self, website_data: WebsiteData) -> list:
        values = []
        strict_transport_security = "strict-transport-security"
        hsts = strict_transport_security in website_data.headers.keys()

        if hsts:
            values += ["hsts"]
            sts = website_data.headers[strict_transport_security]
            if isinstance(sts, list) and len(sts) == 1:
                sts = sts[0]

            for key in ["includesubdomains", "preload"]:
                if key in sts:
                    values += [key]
                else:
                    values += [f"do_not_{key}"]

            regex = re.compile(r"max-age=(\d*)")
            try:
                match = int(regex.match(sts).group(1))
                if match > 10886400:
                    values += ["max-age"]
            except AttributeError:
                values += ["do_not_max-age"]
        else:
            values += ["no_hsts"]
        return values

    def _referrer(self, website_data: WebsiteData) -> list:
        referrer_policy = "referrer-policy"
        rp = referrer_policy in website_data.headers.keys()
        if rp:
            values = [referrer_policy]
        else:
            values = [f"no_{referrer_policy}"]
        return values

    def _font_face(self, website_data: WebsiteData) -> list:
        regex = re.compile(r"@font-face{.*?}")
        matches = re.findall(regex, website_data.html)
        url_regex = re.compile(r"url\((.*?)\)")
        found_fonts = []
        for match in matches:
            url_matches = re.findall(url_regex, match)
            for url_match in url_matches:
                found_fonts.append(url_match)
        return [found_fonts]

    def _input_fields(self, website_data: WebsiteData) -> list:
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
            regex = re.compile(rf"<{input_type}(.*?)>")
            matches = re.findall(regex, website_data.html)
            inputs += [f"{input_type}{match}" for match in matches]
        return [inputs]

    def _start(self, website_data: WebsiteData) -> dict:
        impressum = super()._start(website_data=website_data)[VALUES]
        values = impressum

        value, http_links = self._https_in_url(website_data=website_data)
        values += value

        values += self._hsts(website_data=website_data)

        values += self._referrer(website_data=website_data)

        values += self._font_face(website_data=website_data)

        values += self._input_fields(website_data=website_data)

        return {VALUES: values, "http_links": http_links}
