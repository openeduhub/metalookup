import pytest

from features.MetadataBase import MetadataBase


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
    assert metadatabase.key == ""
    assert metadatabase.url == ""
    assert metadatabase.comment_symbol == ""
    assert not metadatabase.evaluate_header
    assert isinstance(metadatabase._logger, mocker.MagicMock)


"""
--------------------------------------------------------------------------------
"""


def test_start(metadatabase: MetadataBase, mocker):
    html_content = "html_content"
    header = "header"
    metadatabase.key = "test_key"
    _start_spy = mocker.spy(metadatabase, "_start")
    values = metadatabase.start(html_content=html_content, header=header)

    values_has_only_one_key = len(values.keys()) == 1

    assert isinstance(values, dict)
    assert metadatabase.key in values.keys()
    assert values_has_only_one_key
    assert values[metadatabase.key]["values"] == []
    assert values[metadatabase.key]["tag_list_last_modified"] == ""
    assert values[metadatabase.key]["tag_list_expires"] == 0
    assert _start_spy.call_count == 1
    assert _start_spy.call_args_list[0][1] == {
        html_content: html_content,
        header: header,
    }

    _ = metadatabase.start(html_content=html_content)
    assert _start_spy.call_args_list[1][1] == {
        html_content: html_content,
        header: {},
    }


"""
--------------------------------------------------------------------------------
"""


def test_under_start(metadatabase: MetadataBase, mocker):
    html_content = "html_content"
    header = "header"
    processed_header = {header: header}

    work_header_spy = mocker.spy(metadatabase, "_work_header")
    work_html_content_spy = mocker.spy(metadatabase, "_work_html_content")

    metadatabase.evaluate_header = False
    values = metadatabase._start(
        html_content=html_content, header=processed_header
    )

    assert isinstance(values, dict)
    assert work_header_spy.call_count == 0
    assert work_html_content_spy.call_count == 1

    metadatabase.evaluate_header = True
    _ = metadatabase._start(html_content=html_content, header=processed_header)
    assert work_header_spy.call_count == 1
    assert work_html_content_spy.call_count == 1


"""
--------------------------------------------------------------------------------
"""


def test_setup(metadatabase: MetadataBase, mocker):
    metadatabase._download_tag_list = mocker.MagicMock()
    extract_date_from_list_spy = mocker.spy(
        metadatabase, "_extract_date_from_list"
    )
    prepare_tag_spy = mocker.spy(metadatabase, "_prepare_tag_list")

    metadatabase.setup()
    assert metadatabase._download_tag_list.call_count == 0
    assert extract_date_from_list_spy.call_count == 0
    assert prepare_tag_spy.call_count == 0

    metadatabase.url = "hello"
    metadatabase.setup()
    assert metadatabase._download_tag_list.call_count == 1
    assert extract_date_from_list_spy.call_count == 1
    assert prepare_tag_spy.call_count == 1
