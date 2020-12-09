import asyncio
import json
from json import JSONDecodeError

from aiohttp import ClientSession

from features.metadata_base import MetadataBase, ProbabilityDeterminationMethod
from features.website_manager import WebsiteData
from lib.constants import VALUES


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
        strategy: str = "desktop",
    ):
        _categories = [
            "accessibility",
            "performance",
            "seo",
            "pwa",
            "best-practices",
        ]
        params = {
            "url": f"{website_data.url}",
            "category": _categories,
            "strategy": strategy,
        }
        pagespeed_url = (
            "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        )

        process = await session.request(
            method="GET", url=pagespeed_url, params=params
        )
        html = await process.text()

        try:
            result = json.loads(html)
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
                score = [-1]
            else:
                score = [
                    result["lighthouseResult"]["categories"][score_key][
                        "score"
                    ]
                    for score_key in _categories
                ]
        except KeyError:
            self._logger.exception(
                f"Key error when accessing PageSpeedOnline result for {website_data.url}. "
                f"Returns {result}"
            )
            score = [-1]

        return score

    async def _astart(self, website_data: WebsiteData) -> dict:
        async with ClientSession() as session:
            score = await asyncio.gather(
                self._execute_api_call(
                    website_data=website_data,
                    session=session,
                    strategy="desktop",
                ),
                self._execute_api_call(
                    website_data=website_data,
                    session=session,
                    strategy="mobile",
                ),
            )
        score = [element for sublist in score for element in sublist]
        return {VALUES: score}
