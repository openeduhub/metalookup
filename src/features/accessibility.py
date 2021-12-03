import asyncio
import json

from aiohttp import ClientConnectorError, ClientSession

from app.models import Explanation, StarCase
from features.metadata_base import MetadataBase
from features.website_manager import WebsiteData
from lib.constants import (
    ACCESSIBILITY,
    DESKTOP,
    MESSAGE_URL,
    MOBILE,
    SCORE,
    VALUES,
)
from lib.settings import ACCESSIBILITY_TIMEOUT, ACCESSIBILITY_URL


class Accessibility(MetadataBase):
    decision_threshold = 0.8
    call_async = True

    def extract_score(self, score_text: str) -> float:
        try:
            score = float(json.loads(score_text)[SCORE][0])
        except (KeyError, ValueError, TypeError):
            self._logger.exception(f"Score output was faulty: '{score_text}'.")
            score = -1
        return score

    async def _execute_api_call(
        self,
        website_data: WebsiteData,
        session: ClientSession,
        strategy: str = DESKTOP,
    ) -> float:
        params = {
            MESSAGE_URL: website_data.url,
            "category": ACCESSIBILITY,
            "strategy": strategy,
        }
        container_url = f"{ACCESSIBILITY_URL}/{ACCESSIBILITY}"

        try:
            process = await session.get(
                url=container_url, timeout=ACCESSIBILITY_TIMEOUT, json=params
            )
        except (
            asyncio.exceptions.TimeoutError,
            ClientConnectorError,
            OSError,
        ) as err:
            self._logger.exception(
                f"Timeout for url {container_url} after 60s: {err.args}, {str(err)}"
            )
            process = None

        score = -1
        if process is not None and process.status == 200:
            score_text = await process.text()
            score = self.extract_score(score_text)
        return score

    async def _astart(self, website_data: WebsiteData) -> dict:
        async with ClientSession() as session:
            score = await asyncio.gather(
                *[
                    self._execute_api_call(
                        website_data=website_data,
                        session=session,
                        strategy=strategy,
                    )
                    for strategy in [DESKTOP, MOBILE]
                ]
            )
        score = [value for value in score if value != -1]
        return {VALUES: score}

    def _decide(
        self, website_data: WebsiteData
    ) -> tuple[StarCase, list[Explanation]]:
        decision, explanation = self._get_default_decision()
        if website_data.values:
            mean = round(
                sum(website_data.values) / (len(website_data.values)), 2
            )
            decision = self._get_inverted_decision(mean)
            if decision == StarCase.ZERO:
                explanation = [Explanation.AccessibilityTooLow]
            elif decision == StarCase.ONE:
                # TODO unhandled case
                explanation = [Explanation.AccessibilityServiceReturnedFailure]
            else:
                explanation = [Explanation.AccessibilitySuitable]
        return decision, explanation
