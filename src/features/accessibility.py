import asyncio
import json
import subprocess
import time
from json import JSONDecodeError

from aiohttp import ClientSession

from features.metadata_base import MetadataBase, ProbabilityDeterminationMethod
from features.website_manager import WebsiteData
from lib.constants import ACCESSIBILITY, DESKTOP, MESSAGE_URL, SCORE, VALUES


class Accessibility(MetadataBase):
    probability_determination_method = (
        ProbabilityDeterminationMethod.FIRST_VALUE
    )
    decision_threshold = 0.8
    call_async = True

    async def _execute_api_call(
        self,
        website_data: WebsiteData,
        session: ClientSession,
        strategy: str = DESKTOP,
    ) -> list:
        params = {
            MESSAGE_URL: website_data.url,
            "category": ACCESSIBILITY,
            "strategy": strategy,
        }
        container_url = f"http://{ACCESSIBILITY}:5058/{ACCESSIBILITY}"

        process = await session.get(url=container_url, timeout=60, json=params)

        score_text = await process.text()

        try:
            score = [float(json.loads(score_text)[SCORE])]
        except (KeyError, ValueError, TypeError):
            self._logger.exception(f"Score output was: '{score_text}'")
            score = [-1]

        return score

    async def _astart(self, website_data: WebsiteData) -> dict:
        async with ClientSession() as session:
            score = await asyncio.gather(
                self._execute_api_call(
                    website_data=website_data,
                    session=session,
                    strategy=DESKTOP,
                ),
                self._execute_api_call(
                    website_data=website_data,
                    session=session,
                    strategy="mobile",
                ),
            )
        score = [element for sublist in score for element in sublist]
        return {VALUES: score}
