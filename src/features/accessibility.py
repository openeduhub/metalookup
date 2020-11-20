import json
from json import JSONDecodeError

import requests

from features.metadata_base import MetadataBase, ProbabilityDeterminationMethod
from features.website_manager import WebsiteData
from lib.constants import VALUES


class Accessibility(MetadataBase):
    probability_determination_method = (
        ProbabilityDeterminationMethod.FIRST_VALUE
    )
    decision_threshold = 0.8

    def _start(self, website_data: WebsiteData) -> dict:
        process = requests.get(
            "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
            params={
                "url": f"{website_data.url}",
                "category": "ACCESSIBILITY",
                "key": "AIzaSyCdJDuGP-rdtIid8kIm2-aaMQRNcgomyIM",
            },
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
                    f"{result['error']['code']}: {result['error']['message']}"
                )
                score = -1
            else:
                score = result["lighthouseResult"]["categories"][
                    "accessibility"
                ]["score"]
        except KeyError:
            self._logger.exception(
                f"Key error when accessing PageSpeedOnline result for {website_data.url}. "
                f"Returns {result}"
            )
            score = -1
        return {VALUES: [score]}
