import json
from json import JSONDecodeError

import requests

from features.metadata_base import MetadataBase
from features.website_manager import WebsiteData
from lib.constants import VALUES


class Accessibility(MetadataBase):
    def _start(self, website_data: WebsiteData) -> dict:
        process = requests.get(
            "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
            params={"url": f"{website_data.url}", "category": "ACCESSIBILITY"},
        )
        try:
            result = json.loads(process.content.decode())
        except JSONDecodeError:
            self._logger.exception(
                f"JSONDecodeError error when accessing PageSpeedOnline result for {website_data.url}."
            )
            result = {}

        try:
            if "error" in result.keys():
                self._logger.error(
                    result["error"]["code"], result["error"]["message"]
                )
                score = None
            else:
                score = result["lighthouseResult"]["categories"][
                    "accessibility"
                ]["score"]
        except KeyError:
            self._logger.exception(
                f"Key error when accessing PageSpeedOnline result for {website_data.url}. "
                f"Returns {result}"
            )
            score = None
        return {VALUES: score}
