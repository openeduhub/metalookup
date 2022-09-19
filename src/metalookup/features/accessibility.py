import asyncio
import logging
from concurrent.futures import Executor

from aiohttp import ClientSession
from fastapi import HTTPException
from pydantic import BaseModel

from metalookup.app.models import Explanation, StarCase
from metalookup.core.content import Content
from metalookup.core.extractor import Extractor
from metalookup.lib.settings import LIGHTHOUSE_TIMEOUT, LIGHTHOUSE_URL
from metalookup.lib.tools import runtime

logger = logging.getLogger(__name__)

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

    async def extract(self, content: Content, executor: Executor) -> tuple[StarCase, Explanation, AccessibilityScores]:
        scores = await asyncio.gather(
            *[self._execute_api_call(url=content.url, strategy=strategy) for strategy in [_DESKTOP, _MOBILE]],
            # see https://docs.python.org/3/library/asyncio-task.html#running-tasks-concurrently
            return_exceptions=True,
        )
        if any(isinstance(s, BaseException) for s in scores):
            logger.warning(f"Failed to extract with lighthouse: {scores}")
            raise HTTPException(status_code=500, detail="Failed to receive scores from lighthouse")

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

    async def _execute_api_call(self, url: str, strategy: str = "desktop") -> float:
        params = {
            "url": url,
            "category": _ACCESSIBILITY,
            "strategy": strategy,
        }
        try:
            async with ClientSession() as session:
                with runtime() as t:
                    response = await session.post(
                        url=f"{self.lighthouse_url}/{_ACCESSIBILITY}", timeout=self.lighthouse_timeout, json=params
                    )
                logger.debug(f"Fetched accessibility for {strategy} in {t():5.2f}s")
        except asyncio.exceptions.TimeoutError:
            raise RuntimeError(
                f"Lighthouse request for {strategy=} and {url=} timed out after {self.lighthouse_timeout} seconds"
            )
        content = await response.json()
        if response.status == 200:
            # expected result looks like {"score": [0.123]}
            return float(content["score"][0])
        elif response.status == 502:
            detail = content.get("detail", "Unknown Error")
            logger.debug(f"Lighthouse request for {url} failed: {detail}")
            # received for content that is not HTML.
            raise HTTPException(status_code=400, detail=f"Cannot analyze non-html content for accessibility: {detail}")
        else:
            raise RuntimeError(f"Request to lighthouse failed with {response.status}: {await response.text()}")
