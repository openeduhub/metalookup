from concurrent.futures import Executor

from metalookup.app.models import Explanation, StarCase
from metalookup.core.extractor import Extractor
from metalookup.core.website_manager import WebsiteData

_NO_KNOCKOUT_MATCH_FOUND = "No knockout match found"
_KNOCKOUT_MATCH_FOUND = "Found knockout match"


class IFrameEmbeddable(Extractor[set[str]]):
    key = "iframe_embeddable"

    async def setup(self) -> None:
        pass

    async def extract(self, site: WebsiteData, executor: Executor) -> tuple[StarCase, Explanation, set[str]]:
        # site headers is expected to be a dict[str,str] where the values potentially are ';' separated lists
        # See https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options for docs.
        x_frame_options = {
            value.strip().upper() for value in site.headers.get("x-frame-options", "").split(";") if value != ""
        }
        false_list = ["SAMEORIGIN", "DENY"]
        knockout_found = any(knockout in x_frame_options for knockout in false_list)
        stars = StarCase.ZERO if knockout_found else StarCase.FIVE
        explanation = _KNOCKOUT_MATCH_FOUND if knockout_found else _NO_KNOCKOUT_MATCH_FOUND
        return stars, explanation, x_frame_options
