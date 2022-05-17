import asyncio

import adblockparser
import pytest

from app.models import Explanation, StarCase
from core.metadata_base import MetadataBase, ProbabilityDeterminationMethod
from tests.integration.features_integration_test import mock_website_data


@pytest.fixture
def metadatabase(mocker):
    logger = mocker.MagicMock()
    return MetadataBase(logger)


"""
--------------------------------------------------------------------------------
"""


def test_init(metadatabase: MetadataBase, mocker):
    assert metadatabase.tag_list == []
    assert metadatabase.tag_list_last_modified == ""
    assert metadatabase.tag_list_expires == 0
    assert metadatabase.url == ""
    assert metadatabase.comment_symbol == ""
    assert not metadatabase.evaluate_header
    assert isinstance(metadatabase._logger, mocker.MagicMock)


"""
--------------------------------------------------------------------------------
"""


def test_start(metadatabase: MetadataBase, mocker):
    site = mock_website_data()
    metadatabase.key = "test_key"
    start_spy = mocker.spy(metadatabase, "_start")
    _, values, _, _ = asyncio.run(metadatabase.start(site=site))

    assert isinstance(values, list)
    assert values == []

    assert start_spy.call_count == 1
    assert start_spy.call_args_list[0][1] == {"website_data": site}

    _ = asyncio.run(metadatabase.start(site))
    assert start_spy.call_args_list[1][1] == {"website_data": site}


"""
--------------------------------------------------------------------------------
"""


def test_under_start(metadatabase: MetadataBase, mocker):
    work_header_spy = mocker.spy(metadatabase, "_work_header")
    work_html_content_spy = mocker.spy(metadatabase, "_work_html_content")

    metadatabase.evaluate_header = False
    website_data = mock_website_data()

    values = asyncio.run(metadatabase._start(website_data=website_data))

    assert isinstance(values, list)
    assert work_header_spy.call_count == 0
    assert work_html_content_spy.call_count == 1

    metadatabase.evaluate_header = True
    _ = asyncio.run(metadatabase._start(website_data=website_data))
    assert work_header_spy.call_count == 1
    assert work_html_content_spy.call_count == 1


"""
--------------------------------------------------------------------------------
"""


@pytest.mark.asyncio
async def test_setup(metadatabase: MetadataBase, mocker):
    metadatabase._download_tag_list = mocker.AsyncMock(return_value=[])
    metadatabase._download_multiple_tag_lists = mocker.AsyncMock(
        return_value=[]
    )
    extract_date_from_list_spy = mocker.spy(
        metadatabase, "_extract_date_from_list"
    )
    prepare_tag_spy = mocker.spy(metadatabase, "_prepare_tag_list")

    await metadatabase.setup()
    assert metadatabase._download_tag_list.call_count == 0
    assert metadatabase._download_multiple_tag_lists.call_count == 0
    assert extract_date_from_list_spy.call_count == 0
    assert prepare_tag_spy.call_count == 0

    metadatabase.url = "hello"
    await metadatabase.setup()
    assert metadatabase._download_tag_list.call_count == 1
    assert metadatabase._download_multiple_tag_lists.call_count == 0
    assert extract_date_from_list_spy.call_count == 0
    assert prepare_tag_spy.call_count == 0

    metadatabase.url = ""
    metadatabase.urls = ["Hello1", "Hello2"]
    metadatabase._download_tag_list.return_value = ["empty_list"]
    await metadatabase.setup()
    assert metadatabase._download_tag_list.call_count == 1
    assert metadatabase._download_multiple_tag_lists.call_count == 1
    assert extract_date_from_list_spy.call_count == 0
    assert prepare_tag_spy.call_count == 0

    metadatabase.tag_list = ["empty_list"]
    metadatabase.urls = []
    await metadatabase.setup()
    assert metadatabase._download_tag_list.call_count == 1
    assert metadatabase._download_multiple_tag_lists.call_count == 1
    assert extract_date_from_list_spy.call_count == 1
    assert prepare_tag_spy.call_count == 1


"""
--------------------------------------------------------------------------------
"""


def _create_sample_easylist() -> list:
    easylist = [
        "! *** easylist:easylist/easylist_general_block.txt ***",
        r"/adv_horiz.",
        r"@@||imx.to/dropzone.js$script",
        r"||testimx.to/dropzone.js$script",
        r"||testimx2.to/dropzone.js",
    ]

    return easylist


def _create_sample_urls() -> list:
    url_to_be_blocked = [
        ("https://www.dictionary.com/", False),
        ("/adv_horiz.", True),
        ("imx.to/dropzone.js", False),
        ("testimx.to/dropzone.js", False),
        ("testimx2.to/dropzone.js", True),
    ]
    return url_to_be_blocked


def test_easylist_filter():
    urls_to_be_blocked = _create_sample_urls()

    rules = adblockparser.AdblockRules(_create_sample_easylist())

    for url, to_be_blocked in urls_to_be_blocked:
        result = rules.should_block(url)  # "http://ads.example.com"
        assert result == to_be_blocked


"""
--------------------------------------------------------------------------------
"""


@pytest.mark.parametrize(
    "values, decision_threshold, expected_decision, expected_explanation",
    [
        ([], -1, StarCase.FIVE, [Explanation.FoundNoListMatches]),
        (
            [0.5],
            -1,
            StarCase.ZERO,
            [Explanation.FoundListMatches],
        ),
        (
            [0.5, 1],
            -1,
            StarCase.ZERO,
            [Explanation.FoundListMatches],
        ),
        ([0.5], 0.5, StarCase.ZERO, [Explanation.FoundListMatches]),
        ([0.5], 1, StarCase.ZERO, [Explanation.FoundListMatches]),
        ([], 1, StarCase.FIVE, [Explanation.FoundNoListMatches]),
    ],
)
def test_decide_single(
    metadatabase: MetadataBase,
    values,
    decision_threshold,
    expected_decision,
    expected_explanation,
):
    website_data = mock_website_data()

    website_data.values = values
    metadatabase.decision_threshold = decision_threshold
    metadatabase.probability_determination_method = (
        ProbabilityDeterminationMethod.SINGLE_OCCURRENCE
    )
    decision, explanation = metadatabase._decide(website_data=website_data)

    assert decision == expected_decision
    assert explanation == expected_explanation


"""
--------------------------------------------------------------------------------
"""


@pytest.mark.parametrize(
    "values, decision_threshold, expected_decision, raw_links, expected_explanation",
    [
        (
            [0.5],
            0.01,
            StarCase.FIVE,
            [],
            [Explanation.FoundNoListMatches],
        ),
        (
            [0.5, 1, 1, 1],
            0,
            StarCase.ZERO,
            [1, 1, 1, 1],
            [Explanation.FoundListMatches],
        ),
        (
            [0.5],
            0,
            StarCase.ZERO,
            [1, 1, 1, 1],
            [Explanation.FoundListMatches],
        ),
        (
            [0.5],
            0.5,
            StarCase.FIVE,
            [1, 1, 1, 1],
            [Explanation.FoundListMatches],
        ),
    ],
)
def test_decide_number_of_elements(
    metadatabase: MetadataBase,
    values,
    decision_threshold,
    expected_decision,
    raw_links,
    expected_explanation,
):
    website_data = mock_website_data()

    website_data.values = values
    website_data.raw_links = raw_links
    metadatabase.decision_threshold = decision_threshold
    metadatabase.probability_determination_method = (
        ProbabilityDeterminationMethod.NUMBER_OF_ELEMENTS
    )
    decision, explanation = metadatabase._decide(website_data=website_data)

    assert decision == expected_decision
    assert explanation == expected_explanation


"""
--------------------------------------------------------------------------------
"""


@pytest.mark.parametrize(
    "values, decision_threshold, expected_decision,  false_list, expected_explanation",
    [
        (
            [0.5],
            1,
            StarCase.FIVE,
            [0],
            [Explanation.NoKnockoutMatchFound],
        ),
        (
            [0.5],
            1,
            StarCase.ZERO,
            [0.5],
            [Explanation.KnockoutMatchFound],
        ),
        (
            [0.5, 0.1, 0, "hello"],
            1,
            StarCase.ZERO,
            ["hello"],
            [Explanation.KnockoutMatchFound],
        ),
        (
            [0.5, 0.1, 0, "hello"],
            1,
            StarCase.FIVE,
            ["hell"],
            [Explanation.NoKnockoutMatchFound],
        ),
        (
            [0.5, 0.1, 0, "hello"],
            1,
            StarCase.FIVE,
            ["0"],
            [Explanation.NoKnockoutMatchFound],
        ),
        (
            [0.5, 0.1, 0, "hello"],
            1,
            StarCase.ZERO,
            ["0", "hello"],
            [Explanation.KnockoutMatchFound],
        ),
    ],
)
def test_false_list(
    metadatabase: MetadataBase,
    values,
    decision_threshold,
    expected_decision,
    false_list,
    expected_explanation,
):
    website_data = mock_website_data()

    website_data.values = values
    metadatabase.false_list = false_list
    metadatabase.decision_threshold = decision_threshold
    metadatabase.probability_determination_method = (
        ProbabilityDeterminationMethod.FALSE_LIST
    )
    decision, explanation = metadatabase._decide(website_data=website_data)

    assert decision == expected_decision
    assert explanation == expected_explanation
