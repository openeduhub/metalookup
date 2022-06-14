import pprint

import pytest

from app.models import Input, MetadataTags
from core.metadata_manager import MetadataManager
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
