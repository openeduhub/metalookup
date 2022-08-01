import pprint

import pytest
from fastapi import HTTPException

from metalookup.app.models import Input, MetadataTags
from metalookup.core.metadata_manager import MetadataManager
from tests.conftest import lighthouse_mock, splash_mock


@pytest.fixture
async def manager() -> MetadataManager:
    manager = MetadataManager()
    await manager.setup()
    return manager


@pytest.mark.asyncio
async def test_extract(manager: MetadataManager):
    # intercept the request to the non-running splash and lighthouse container
    # and instead use the checked in response json and a hardcoded score value
    with splash_mock(key="google.com"), lighthouse_mock():
        output = await manager.extract(Input(url="https://www.google.com/"), extra=True)

        print("Extraction result from manager:")
        pprint.pprint(output.dict())

        # check that all extractors worked without exceptions
        for e in manager.extractors:
            assert isinstance(
                getattr(output, e.key), MetadataTags
            ), f"Unexpected output for extractor {e}: {getattr(output, e.key)} "


@pytest.mark.asyncio
async def test_extract_redirect(manager: MetadataManager):
    # intercept the request to the non-running splash and lighthouse container
    # and instead use the checked in response json and a hardcoded score value
    with splash_mock(key="google.de"), lighthouse_mock():
        output = await manager.extract(Input(url="https://google.de"), extra=True)

        print("Extraction result from manager:")
        pprint.pprint(output.dict())

        # check that all extractors worked without exceptions
        for e in manager.extractors:
            assert isinstance(
                getattr(output, e.key), MetadataTags
            ), f"Unexpected output for extractor {e}: {getattr(output, e.key)} "


@pytest.mark.asyncio
async def test_extract_for_404_410(manager: MetadataManager):
    # intercept the request to the non-running splash container
    # and instead use the checked in response json
    with splash_mock(key="wlo-404"), pytest.raises(HTTPException) as exception:
        # as the resource is gone, the har in the splash response will indicate a 404 or 410
        # and the manager should signal this to the user by responding with a 502.
        await manager.extract(Input(url="https://wirlernenonline.de/does-not-exist.html"), extra=True)
    assert exception.value.status_code == 502


@pytest.mark.asyncio
async def test_extract_splash_unavailable(manager: MetadataManager):
    with pytest.raises(HTTPException) as exception:
        # as splash is not running, we should get some Connection exception
        # which the manager should translate into an HTTPException
        await manager.extract(Input(url="https://www.google.com"), extra=True)
    assert exception.value.status_code == 500


@pytest.mark.asyncio
async def test_extract_non_html_content(manager: MetadataManager):
    # intercept the request to the non-running splash and lighthouse container
    # and instead use the checked in response json and a hardcoded score value
    with lighthouse_mock(status=502, detail="Non-HTML Content"), splash_mock("wlo-svg-logo"), pytest.raises(
        HTTPException
    ) as exception:
        # as splash is not running, we should get some Connection exception
        # which the manager should translate into an HTTPException
        await manager.extract(
            Input(url="https://wirlernenonline.de/wp-content/themes/wir-lernen-online/src/assets/img/wlo-logo.svg"),
            extra=True,
        )
    assert exception.value.status_code == 400
