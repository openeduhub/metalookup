import json
from concurrent.futures import Executor

import pytest

from metalookup.app.models import StarCase
from metalookup.features.licence import DetectedLicences, Licence, LicenceExtractor
from tests.extractors.conftest import mock_content


def test_serialize_extra():
    """Make sure the extra data can be propperly json serialized"""
    l1 = DetectedLicences(guess=Licence.CC0, counts={Licence.CC_BY_SA: 5, Licence.GSFDL: 1}, total=6)
    # make sure we don't just represent the variant as a number
    # or a string like "Licence.CC_BY_SA"
    assert "CC_BY_SA" in l1.dict()["counts"]
    assert l1 == DetectedLicences.parse_obj(json.loads(l1.json()))


@pytest.mark.asyncio
async def test_extract(executor: Executor):

    content = mock_content(
        url="https://www.google.com", html="Lorem ipsum Creative Commons Zero ... CC BY-SA ... CC BY ... CC0 ..."
    )

    extractor = LicenceExtractor()
    await extractor.setup()
    stars, explanation, extra = await extractor.extract(content=content, executor=executor)
    assert extra.guess == Licence.CC0.value
    assert extra.total == 4
    assert len(extra.counts) == 3
    assert set(extra.counts.keys()) == {Licence.CC0.value, Licence.CC_BY.value, Licence.CC_BY_SA.value}
    assert stars == StarCase.FIVE
    assert isinstance(explanation, str), "Explanation should be a string"
