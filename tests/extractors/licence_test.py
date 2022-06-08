import json
import logging
from concurrent.futures import Executor
from pathlib import Path

import pytest
from tldextract import TLDExtract

from app.models import Input, StarCase
from app.splash_models import SplashResponse
from core.website_manager import WebsiteData
from features.licence import Licence, LicenceExtractor


@pytest.mark.asyncio
async def test_licence_extractor(executor: Executor):
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
    assert extra.guess is Licence.CC0
    assert extra.total == 4
    assert len(extra.counts) == 3
    assert set(extra.counts.keys()) == {Licence.CC0, Licence.CC_BY, Licence.CC_BY_SA}
    assert stars == StarCase.FIVE
    assert isinstance(explanation, str), "Explanation should be a string"
