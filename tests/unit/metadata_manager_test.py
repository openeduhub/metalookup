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
    input = Input(url="https://www.google.com")

    # intercept the request to the non-running splash and lighthouse container
    # and instead use the checked in response json and a hardcoded score value
    with splash_mock(), lighthouse_mock():
        output = await manager.extract(input, extra=True)

        print("Extraction result from manager:")
        pprint.pprint(output.dict())

        # check that all extractors worked without exceptions
        for e in manager.extractors:
            assert isinstance(
                getattr(output, e.key), MetadataTags
            ), f"Unexpected output for extractor {e}: {getattr(output, e.key)} "


@pytest.mark.asyncio
async def test_extract_for_404_410(manager: MetadataManager):
    input = Input(url="https://wirlernenonline.de/does-not-exist.html")

    # intercept the request to the non-running splash container
    # and instead use the checked in response json
    with splash_mock(), pytest.raises(HTTPException) as exception:
        # as the resource is gone, the har in the splash response will indicate a 404 or 410
        # and the manager should signal this to the user by responding with a 502.
        await manager.extract(input, extra=True)
    assert exception.value.status_code == 502
