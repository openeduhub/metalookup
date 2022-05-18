import asyncio
import json

from aiohttp import ClientSession

from app.models import Explanation, StarCase
from core.metadata_base import MetadataBase
from core.website_manager import WebsiteData
from lib.constants import ACCESSIBILITY
from lib.settings import ACCESSIBILITY_TIMEOUT, ACCESSIBILITY_URL

_DESKTOP = "desktop"
_MOBILE = "mobile"


@MetadataBase.with_key()
class Accessibility(MetadataBase):
    star_levels = [0.7, 0.8, 0.85, 0.9, 0.95, 1]

    async def _execute_api_call(
        self,
        website_data: WebsiteData,
        session: ClientSession,
        strategy: str = "desktop",
    ) -> float:
        params = {
            "url": website_data.url,
            "category": ACCESSIBILITY,
            "strategy": strategy,
        }
        container_url = f"{ACCESSIBILITY_URL}/{ACCESSIBILITY}"

        response = await session.get(
            url=container_url, timeout=ACCESSIBILITY_TIMEOUT, json=params
        )

        if response.status == 200:
            return json.loads(await response.text())["score"]
        else:
            raise Exception(
                f"Request to lighthouse failed with {response.status}: {await response.text()}"
            )

    async def _start(self, website_data: WebsiteData) -> list[str]:
        async with ClientSession() as session:
            score = await asyncio.gather(
                *[
                    self._execute_api_call(
                        website_data=website_data,
                        session=session,
                        strategy=strategy,
                    )
                    for strategy in [_DESKTOP, _MOBILE]
                ]
            )
        # take the average score over desktop and mobile.
        # fixme: do not mutate website data.
        website_data.score = (score[0] + score[1]) / 2
        return [str(website_data.score)]

    def _decide(
        self, website_data: WebsiteData
    ) -> tuple[StarCase, list[Explanation]]:
        if score := getattr(website_data, "score", False):
            if score <= self.star_levels[0]:
                return StarCase.ZERO, [Explanation.AccessibilityTooLow]
            elif score <= self.star_levels[1]:
                return StarCase.ONE, [Explanation.AccessibilityTooLow]
            elif score <= self.star_levels[2]:
                return StarCase.TWO, [Explanation.AccessibilityTooLow]
            elif score <= self.star_levels[3]:
                return StarCase.THREE, [Explanation.AccessibilityTooLow]
            elif score <= self.star_levels[4]:
                return StarCase.FOUR, [Explanation.AccessibilitySuitable]
            elif score > self.star_levels[4]:
                return StarCase.FIVE, [Explanation.AccessibilitySuitable]
        else:
            return StarCase.ZERO, [Explanation.none]
