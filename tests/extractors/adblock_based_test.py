import pprint
from collections import namedtuple

import pytest

from metalookup.core.content import Content
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
    with adblock_rules_mock(rules={"/ads/*$image"}):  # avoid downloading external resources to have repeatable tests.
        await feature.setup()
    Request = namedtuple("Request", ["url", "resource_type"])
    content = mock_content(
        url="https://wlo.com",
        requests=[Request(url="https://some-domain.com/ads/123.json", resource_type="script")],  # noqa
    )
    expected = {"https://some-domain.com/ads/123.json"}

    domain = await content.domain()

    _, matches = feature.apply_rules(domain, await content.requests())
    assert matches == expected

    content = mock_content(
        url="https://wlo.com",
        requests=[Request(url="https://some-domain.com/ads/123.json", resource_type="fetch")],  # noqa
    )
    expected = {}

    with runtime() as t:
        stars, explanation, matches = await feature.extract(content, executor=executor)
    assert t() < 10
    assert matches == expected


# @pytest.mark.skip("Intended for manual testing.")
@pytest.mark.asyncio
async def test_blocker_test_site(executor):
    """
    As all adblock based extractors only distinguish by the set of rules
    they download testing one of them here is sufficient...
    """
    feature = Advertisement()
    await feature.setup()

    # This is a site meant to test adblockers. Visit it to check your own setup and see how it works.
    content = Content(url="https://d3ward.github.io/toolz/adblock.html")  # noqa

    domain = await content.domain()

    _, matches = feature.apply_rules(domain, await content.requests())
    requests = await content.requests()
    print(f"Total requests: {len(requests)}")
    print(
        f"'Blocked' requests: {len(matches)}"  # they are not really blocked, but were flagged by the ad block rules :)
    )
    print("Blocked:")
    pprint.pprint(matches)

    for request in await content.requests():
        print(request.method, request.resource_type, request.url)
