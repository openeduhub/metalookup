import pytest

from metalookup.features.adblock_based import Advertisement
from metalookup.lib.tools import runtime
from tests.conftest import adblock_rules_mock
from tests.extractors.conftest import mock_content


@pytest.mark.asyncio
async def test_adblock_based(executor):
    """
    As all adblock based extractors only distinguish by the set of rules
    they download testing one of them here is sufficient...
    """
    feature = Advertisement()
    # overwrite rules with a custom test, rendering the test independent on changes of the downloaded lists.
    with adblock_rules_mock(rules={"/ads/*$script"}):  # avoid downloading external resources to have repeatable tests.
        await feature.setup()

    content = mock_content(html="<script src='https://some-domain.com/ads/123.json'></script>")
    expected = {"https://some-domain.com/ads/123.json"}

    domain = await content.domain()
    links = await content.raw_links()

    _, matches = feature.apply_rules(domain, links)
    assert matches == expected

    with runtime() as t:
        stars, explanation, matches = await feature.extract(content, executor=executor)
    assert t() < 10
    assert matches == expected
