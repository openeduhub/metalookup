import json
import logging
from concurrent.futures import Executor
from pathlib import Path

import pytest
from tldextract import TLDExtract

from app.models import Input, StarCase
from app.splash_models import SplashResponse
from core.website_manager import WebsiteData
from features.licence import DetectedLicences, Licence, LicenceExtractor


def test_serialize_extra():
    """Make sure the extra data can be propperly json serialized"""
    l1 = DetectedLicences(guess=Licence.CC0, counts={Licence.CC_BY_SA: 5, Licence.GSFDL: 1}, total=6)
    # make sure we don't just represent the variant as a number
    # or a string like "Licence.CC_BY_SA"
    assert "CC_BY_SA" in l1.dict()["counts"]
    assert l1 == DetectedLicences.parse_obj(json.loads(l1.json()))


@pytest.mark.asyncio
async def test_extract(executor: Executor):
    with open(Path(__file__).parent.parent / "resources" / "splash-response-google.json", "r") as f:
        splash_response = SplashResponse.parse_obj(json.load(f))
    # we dont want to count "CC BY-SA" as "CC BY"!
    splash_response.html = "Lorem ipsum Creative Commons Zero ... CC BY-SA ... CC BY ... CC0 ..."
    site = await WebsiteData.from_input(
        input=Input(url="https://www.google.com", splash_response=splash_response),
        tld_extractor=TLDExtract(cache_dir=None),
        logger=logging.getLogger(),
    )

    extractor = LicenceExtractor()
    await extractor.setup()
    stars, explanation, extra = await extractor.extract(site=site, executor=executor)
    assert extra.guess == Licence.CC0.value
    assert extra.total == 4
    assert len(extra.counts) == 3
    assert set(extra.counts.keys()) == {Licence.CC0.value, Licence.CC_BY.value, Licence.CC_BY_SA.value}
    assert stars == StarCase.FIVE
    assert isinstance(explanation, str), "Explanation should be a string"
