import subprocess

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
        values = process.content.decode().splitlines()
        return {VALUES: values}


"""

{
  "error": {
    "code": 500,
    "message": "Lighthouse returned error: ERRORED_DOCUMENT_REQUEST. Lighthouse was unable to reliably load the page you requested. Make sure you are testing the correct URL and that the server is properly responding to all requests. (Status code: 404)",
    "errors": [
      {
        "message": "Lighthouse returned error: ERRORED_DOCUMENT_REQUEST. Lighthouse was unable to reliably load the page you requested. Make sure you are testing the correct URL and that the server is properly responding to all requests. (Status code: 404)",
        "domain": "lighthouse",
        "reason": "lighthouseError"
      }
    ]
  }
}

{
  "error": {
    "code": 429,
    "message": "Quota exceeded for quota group 'default' and limit 'Queries per 100 seconds' of service 'pagespeedonline.googleapis.com' for consumer 'project_number:583797351490'.",
    "errors": [
      {
        "message": "Quota exceeded for quota group 'default' and limit 'Queries per 100 seconds' of service 'pagespeedonline.googleapis.com' for consumer 'project_number:583797351490'.",
        "domain": "global",
        "reason": "rateLimitExceeded"
      }
    ],
    "status": "RESOURCE_EXHAUSTED"
  }
}
"""
