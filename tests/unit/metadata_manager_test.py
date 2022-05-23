import json
import pprint
from pathlib import Path
from unittest import mock

import pytest

from app.models import Input, MetadataTags
from app.splash_models import SplashResponse
from core.metadata_manager import MetadataManager


@pytest.fixture
async def manager() -> MetadataManager:
    return await MetadataManager.create()


@pytest.mark.asyncio
async def test_extract(manager: MetadataManager):
    with open(Path(__file__).parent.parent / "splash-response-google.json", "r") as f:
        splash_response = SplashResponse.parse_obj(json.load(f))

    input = Input(
        url="https://google.com",
        splash_response=splash_response,
    )

    async def accessibility_api_call_mock(self, website_data, session, strategy) -> float:  # noqa
        return 0.98

    # intercept the request to the non-running splash and lighthouse container
    # and instead use the checked in response json and a hardcoded score value
    with mock.patch("requests.get"), mock.patch("json.loads", lambda _: splash_response), mock.patch(
        "features.accessibility.Accessibility._execute_api_call",
        accessibility_api_call_mock,
    ):
        output = await manager.extract(input)

        print("Extraction result from manager:")
        pprint.pprint(output.dict())

        # check that all extractors worked without exceptions
        for e in manager.extractors:
            assert isinstance(
                getattr(output, e.key), MetadataTags
            ), f"Unexpected output for extractor {e}: {getattr(output, e.key)} "
