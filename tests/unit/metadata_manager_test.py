import json
import pprint
from pathlib import Path
from unittest import mock

import pytest

from app.communication import Message
from app.splash_models import SplashResponse
from core.metadata_manager import MetadataManager
from features.html_based import Advertisement
from features.javascript import Javascript
from tests.integration.features_integration_test import mock_website_data


@pytest.fixture
async def metadata_manager():
    return await MetadataManager.create()


def test_is_feature_whitelisted_for_cache(mocker, metadata_manager: MetadataManager):
    assert metadata_manager.is_feature_whitelisted_for_cache(Advertisement(mocker.MagicMock()))
    assert metadata_manager.is_feature_whitelisted_for_cache(Javascript(mocker.MagicMock())) is False


@pytest.mark.asyncio
async def test_extract_meta_data(metadata_manager: MetadataManager):
    allow_list = ["accessibility", "paywall"]
    site = mock_website_data()
    extract = await metadata_manager._extract_meta_data(site, allow_list)
    pprint.pprint(extract)

    # should fail as the lighthouse container is not running
    assert "exception" in extract["accessibility"]

    # should succeed
    assert set(extract["paywall"].keys()) == {
        "explanation",
        "star_case",
        "time_required",
        "values",
    }


@pytest.mark.asyncio
async def test_start(metadata_manager: MetadataManager):
    with open(Path(__file__).parent.parent / "splash-response-google.json", "r") as f:
        splash_response = SplashResponse.parse_obj(json.load(f))

    message = Message(
        url="https://google.com",
        splash_response=splash_response,
        whitelist=None,
        bypass_cache=False,
    )

    async def accessibility_api_call_mock(self, website_data, session, strategy) -> float:  # noqa
        return 0.98

    # intercept the request to the non-running splash and lighthouse container
    # and instead use the checked in response json and a hardcoded score value
    with mock.patch("requests.get"), mock.patch("json.loads", lambda _: splash_response), mock.patch(
        "features.accessibility.Accessibility._execute_api_call",
        accessibility_api_call_mock,
    ):
        output = await metadata_manager.start(message)

        print("Extraction result from manager:")
        print(output)

        assert "exception" not in output.keys()
        assert "time_for_extraction" in output.keys()

        # check that all extractors worked without exceptions
        for k, v in filter(lambda i: isinstance(i, dict), output.items()):
            assert "exception" not in v, f"Extractor {k} failed with {v['exception']}"
