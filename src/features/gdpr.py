import re

from features.metadata_base import MetadataBase
from features.website_manager import WebsiteData
from lib.constants import VALUES


class GDPR(MetadataBase):
    tag_list = ["impressum"]

    def _start(self, website_data: WebsiteData) -> dict:
        impressum = super()._start(website_data=website_data)[VALUES]
        values = impressum

        http = "http"
        https = "https"
        https_in_url = https in website_data.url
        if https_in_url:
            values += ["https_in_url"]

        https_in_all_links = [
            True if https in url or http not in url else False
            for url in website_data.raw_links
        ]
        http_links = website_data.raw_links[https_in_all_links.index(False)]
        values += [http_links]

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

            regex = re.compile(r"max-age=(\d*)")
            try:
                match = int(regex.match(sts).group(1))
                if match > 10886400:
                    values += ["max-age"]
            except AttributeError:
                pass

        return {VALUES: values}
