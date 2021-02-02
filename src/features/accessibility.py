import asyncio
import json
from json import JSONDecodeError

from aiohttp import ClientConnectorError, ClientSession

from features.metadata_base import (
    MetadataBase,
    MetadataBaseException,
    ProbabilityDeterminationMethod,
)
from features.website_manager import WebsiteData
from lib.constants import ACCESSIBILITY, DESKTOP, MESSAGE_URL, SCORE, VALUES
from lib.settings import LIGHTHOUSE_API_PORT


class Accessibility(MetadataBase):
    probability_determination_method = (
        ProbabilityDeterminationMethod.FIRST_VALUE
    )
    decision_threshold = 0.8
    call_async = True

    def extract_score(self, score_text, status_code):
        try:
            score = [float(json.loads(score_text)[SCORE])]
        except (JSONDecodeError, KeyError, ValueError, TypeError):
            self._logger.exception(
                f"Score output was: '{score_text}'. HTML response code was '{status_code}'"
            )
            score = [-1]
        return score

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
        container_url = (
            f"http://{ACCESSIBILITY}:{LIGHTHOUSE_API_PORT}/{ACCESSIBILITY}"
        )

        try:
            process = await session.get(
                url=container_url, timeout=60, json=params
            )
        except (ClientConnectorError, ConnectionRefusedError, OSError):
            raise MetadataBaseException(
                "No connection to accessibility container."
            )

        status_code = process.status

        if status_code == 200:
            score_text = await process.text()
        else:
            score_text = ""

        return self.extract_score(score_text, status_code)

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
