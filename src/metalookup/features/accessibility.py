import asyncio
import json
from concurrent.futures import Executor

from aiohttp import ClientSession
from pydantic import BaseModel

from metalookup.app.models import Explanation, StarCase
from metalookup.core.extractor import Extractor
from metalookup.core.website_manager import WebsiteData
from metalookup.lib.settings import LIGHTHOUSE_TIMEOUT, LIGHTHOUSE_URL

_DESKTOP = "desktop"
_MOBILE = "mobile"
_ACCESSIBILITY = "accessibility"

_LIGHTHOUSE_SCORE_SUITABLE = "Lighthouse accessibility score is suitable"
_LIGHTHOUSE_SCORE_TOO_LOW = "Lighthouse accessibility score is too low"


class AccessibilityScores(BaseModel):
    """
    Expose the lighthouse accessibility scores as extractor extra data.
    Scores range from zero to one, higher is better.
    """

    mobile_score: float
    desktop_score: float
    average_score: float


class Accessibility(Extractor[AccessibilityScores]):
    key = _ACCESSIBILITY

    def __init__(self, lighthouse_timeout: int = LIGHTHOUSE_TIMEOUT, lighthouse_url: str = LIGHTHOUSE_URL):
        """
        :param lighthouse_timeout: The timeout in seconds for requests issued to the lighthouse service.
        :param lighthouse_url: The url of the lighthouse service.
        """
        self.lighthouse_timeout = lighthouse_timeout
        self.lighthouse_url = lighthouse_url
        self.star_levels = [0.7, 0.8, 0.85, 0.9, 0.95]

    async def setup(self):
        pass

    async def extract(self, site: WebsiteData, executor: Executor) -> tuple[StarCase, Explanation, AccessibilityScores]:
        async with ClientSession() as session:

            scores = await asyncio.gather(
                *[
                    self._execute_api_call(url=site.url, session=session, strategy=strategy)
                    for strategy in [_DESKTOP, _MOBILE]
                ]
            )

            scores = AccessibilityScores(
                desktop_score=scores[0], mobile_score=scores[1], average_score=(scores[0] + scores[1]) / 2
            )

            if scores.average_score <= self.star_levels[0]:
                return StarCase.ZERO, _LIGHTHOUSE_SCORE_TOO_LOW, scores
            elif scores.average_score <= self.star_levels[1]:
                return StarCase.ONE, _LIGHTHOUSE_SCORE_TOO_LOW, scores
            elif scores.average_score <= self.star_levels[2]:
                return StarCase.TWO, _LIGHTHOUSE_SCORE_TOO_LOW, scores
            elif scores.average_score <= self.star_levels[3]:
                return StarCase.THREE, _LIGHTHOUSE_SCORE_TOO_LOW, scores
            elif scores.average_score <= self.star_levels[4]:
                return StarCase.FOUR, _LIGHTHOUSE_SCORE_SUITABLE, scores
            else:  # scores.average_score > self.star_levels[4]:
                return StarCase.FIVE, _LIGHTHOUSE_SCORE_SUITABLE, scores

    async def _execute_api_call(self, url: str, session: ClientSession, strategy: str = "desktop") -> float:
        params = {
            "url": url,
            "category": _ACCESSIBILITY,
            "strategy": strategy,
        }
        try:
            response = await session.get(
                url=f"{self.lighthouse_url}/{_ACCESSIBILITY}", timeout=self.lighthouse_timeout, json=params
            )
        except asyncio.exceptions.TimeoutError:
            raise RuntimeError(
                f"Lighthouse request for {strategy=} and {url=} timed out after {self.lighthouse_timeout} seconds"
            )

        if response.status == 200:
            # expected result looks like {"score": [0.123]}
            return float(json.loads(await response.text())["score"][0])
        raise RuntimeError(f"Request to lighthouse failed with {response.status}: {await response.text()}")
