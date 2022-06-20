import adblockparser
import pytest

from app.models import StarCase
from core.extractor import MetadataBase, ProbabilityDeterminationMethod
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
    assert metadatabase.comment_symbol == ""
    assert not metadatabase.evaluate_header
    assert isinstance(metadatabase._logger, mocker.MagicMock)


"""
--------------------------------------------------------------------------------
"""


@pytest.mark.asyncio
async def test_start(metadatabase: MetadataBase, mocker):
    site = await mock_website_data()
    metadatabase.key = "test_key"
    start_spy = mocker.spy(metadatabase, "_start")
    _, values, _, _ = await metadatabase.start(site=site)

    assert isinstance(values, list)
    assert values == []

    assert start_spy.call_count == 1
    assert start_spy.call_args_list[0][1] == {"website_data": site}

    _ = await metadatabase.start(site)
    assert start_spy.call_args_list[1][1] == {"website_data": site}


"""
--------------------------------------------------------------------------------
"""


@pytest.mark.asyncio
async def test_under_start(metadatabase: MetadataBase, mocker):
    work_header_spy = mocker.spy(metadatabase, "_work_header")
    work_html_content_spy = mocker.spy(metadatabase, "_work_html_content")

    metadatabase.evaluate_header = False
    website_data = await mock_website_data()

    values = await metadatabase._start(website_data=website_data)

    assert isinstance(values, list)
    assert work_header_spy.call_count == 0
    assert work_html_content_spy.call_count == 1

    metadatabase.evaluate_header = True
    await metadatabase._start(website_data=website_data)
    assert work_header_spy.call_count == 1
    assert work_html_content_spy.call_count == 1


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
    "values, decision_threshold, expected_decision",
    [
        ([], -1, StarCase.FIVE),  # ,[Explanation.FoundNoListMatches]),
        ([0.5], -1, StarCase.ZERO),  # [Explanation.FoundListMatches],
        ([0.5, 1], -1, StarCase.ZERO),  # ,[Explanation.FoundListMatches],
        ([0.5], 0.5, StarCase.ZERO),  # ,[Explanation.FoundListMatches]),
        ([0.5], 1, StarCase.ZERO),  # ,[Explanation.FoundListMatches]),
        ([], 1, StarCase.FIVE),  # , [Explanation.FoundNoListMatches]),
    ],
)
@pytest.mark.asyncio
async def test_decide_single(metadatabase: MetadataBase, values, decision_threshold, expected_decision):
    website_data = await mock_website_data()

    website_data.values = values
    metadatabase.decision_threshold = decision_threshold
    metadatabase.probability_determination_method = ProbabilityDeterminationMethod.SINGLE_OCCURRENCE
    decision, explanation = metadatabase._decide(website_data=website_data)

    assert decision == expected_decision


"""
--------------------------------------------------------------------------------
"""


@pytest.mark.parametrize(
    "values, decision_threshold, expected_decision, raw_links",
    [
        ([0.5], 0.01, StarCase.FIVE, []),
        ([0.5, 1, 1, 1], 0, StarCase.ZERO, [1, 1, 1, 1]),
        ([0.5], 0, StarCase.ZERO, [1, 1, 1, 1]),
        ([0.5], 0.5, StarCase.FIVE, [1, 1, 1, 1]),
    ],
)
@pytest.mark.asyncio
async def test_decide_number_of_elements(
    metadatabase: MetadataBase,
    values,
    decision_threshold,
    expected_decision,
    raw_links,
):
    website_data = await mock_website_data()

    website_data.values = values
    website_data.raw_links = raw_links
    metadatabase.decision_threshold = decision_threshold
    metadatabase.probability_determination_method = ProbabilityDeterminationMethod.NUMBER_OF_ELEMENTS
    decision, explanation = metadatabase._decide(website_data=website_data)

    assert decision == expected_decision


"""
--------------------------------------------------------------------------------
"""


@pytest.mark.parametrize(
    "values, decision_threshold, expected_decision,  false_list",
    [
        ([0.5], 1, StarCase.FIVE, [0]),
        ([0.5], 1, StarCase.ZERO, [0.5]),
        ([0.5, 0.1, 0, "hello"], 1, StarCase.ZERO, ["hello"]),
        ([0.5, 0.1, 0, "hello"], 1, StarCase.FIVE, ["hell"]),
        ([0.5, 0.1, 0, "hello"], 1, StarCase.FIVE, ["0"]),
        ([0.5, 0.1, 0, "hello"], 1, StarCase.ZERO, ["0", "hello"]),
    ],
)
@pytest.mark.asyncio
async def test_false_list(
    metadatabase: MetadataBase,
    values,
    decision_threshold,
    expected_decision,
    false_list,
):
    website_data = await mock_website_data()

    website_data.values = values
    metadatabase.false_list = false_list
    metadatabase.decision_threshold = decision_threshold
    metadatabase.probability_determination_method = ProbabilityDeterminationMethod.FALSE_LIST
    decision, explanation = metadatabase._decide(website_data=website_data)

    assert decision == expected_decision
