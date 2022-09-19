import pprint
from unittest import mock

import pytest
from fastapi import HTTPException

from metalookup.app.models import Input, MetadataTags
from metalookup.core.metadata_manager import MetadataManager
from tests.conftest import adblock_rules_mock, lighthouse_mock, playwright_mock


@pytest.fixture
async def manager() -> MetadataManager:
    manager = MetadataManager()
    with adblock_rules_mock(rules=set()):
        await manager.setup()
    return manager


@pytest.mark.asyncio
async def test_extract(manager: MetadataManager):
    with playwright_mock(key="google.com"), lighthouse_mock():
        output = await manager.extract(Input(url="https://www.google.com/"), extra=True)

        print("Extraction result from manager:")
        pprint.pprint(output.dict())

        # check that all extractors worked without exceptions
        for e in manager.extractors:
            assert isinstance(
                getattr(output, e.key), MetadataTags
            ), f"Unexpected output for extractor {e}: {getattr(output, e.key)} "


@pytest.mark.asyncio
async def test_extract_for_404_410(manager: MetadataManager):
    with playwright_mock(key="wlo-404"), pytest.raises(HTTPException) as exception:
        # as the resource is gone, the playwright response will indicate a 404 or 410
        # and the manager should signal this to the user by responding with a 502.
        await manager.extract(Input(url="https://wirlernenonline.de/does-not-exist.html"), extra=True)
    assert exception.value.status_code == 502


@pytest.mark.asyncio
async def test_extract_playwright_unavailable(manager: MetadataManager):
    with pytest.raises(HTTPException) as exception, lighthouse_mock(), mock.patch(
        # make sure we trigger an exception by changing the configured value to something nonsensical
        "metalookup.core.content.PLAYWRIGHT_WS_ENDPOINT",
        "ws://invalid-name:3001",
    ):
        # as playwright is not reachable, we should get some Connection exception
        # which the manager should translate into an HTTPException
        await manager.extract(Input(url="https://www.google.com"), extra=True)
    assert exception.value.status_code == 500


@pytest.mark.asyncio
async def test_extract_lighthouse_unavailable(manager: MetadataManager):
    with pytest.raises(HTTPException) as exception, playwright_mock(key="google.com"):
        # as lighthouse is not running, we should get some Connection exception
        # which the manager should translate into an HTTPException
        await manager.extract(Input(url="https://www.google.com"), extra=True)
    assert exception.value.status_code == 500


@pytest.mark.asyncio
async def test_extract_non_html_content(manager: MetadataManager):
    # intercept the request to the non-running lighthouse container and pretend that lighthouse would give an
    # accessibility rating for non html content because we want to test the manager here.
    with lighthouse_mock(), pytest.raises(HTTPException) as exception:
        await manager.extract(
            Input(url="https://wirlernenonline.de/wp-content/themes/wir-lernen-online/src/assets/img/wlo-logo.svg"),
            extra=True,
        )
    assert exception.value.status_code == 400
