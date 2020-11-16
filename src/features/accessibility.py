import json

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
        result = json.loads(process.content.decode())
        if "error" in result.keys():
            self._logger.error(
                result["error"]["code"], result["error"]["message"]
            )
            score = None
        else:
            score = result["lighthouseResult"]["categories"]["accessibility"][
                "score"
            ]
        return {VALUES: score}
