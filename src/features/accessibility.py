import asyncio
import json
import subprocess
import time
from json import JSONDecodeError

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
        strategy: str = "desktop",
    ):
        _categories = [
            "accessibility",
            "performance",
            "seo",
            "pwa",
            "best-practices",
        ]

        cmd = [
            "docker",
            "run",
            "femtopixel/google-lighthouse",
            f"{website_data.url}",
            f"--emulated-form-factor={strategy}",
            "--output=json",
            "--quiet",
        ]

        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        output = []

        for line in iter(p.stdout.readline, b""):
            output.append(line.decode())
        output = "".join(output)

        try:
            result = json.loads(output)
        except JSONDecodeError:
            self._logger.exception(
                f"JSONDecodeError error when accessing PageSpeedOnline result for {website_data.url}."
            )
            result = {}

        try:
            if "runtimeError" in result.keys():
                self._logger.error(
                    f"{result['runtimeError']['code']}: {result['runtimeError']['message']}"
                )
                score = [-1]
            else:
                score = [
                    result["categories"][score_key]["score"]
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
        score = await asyncio.gather(
            self._execute_api_call(
                website_data=website_data,
                strategy="desktop",
            ),
            self._execute_api_call(
                website_data=website_data,
                strategy="mobile",
            ),
        )
        score = [element for sublist in score for element in sublist]
        return {VALUES: score}
