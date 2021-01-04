import json
from json import JSONDecodeError

import pytest
import requests
from test_libs import (
    DOCKER_TEST_HEADERS,
    DOCKER_TEST_URL,
    _build_and_run_docker,
)


@pytest.mark.skip(
    reason="This test takes a lot of time, depending on payload etc. Execute manually."
)
def test_e2e():
    url = DOCKER_TEST_URL + "extract_meta"

    payload = '{"url": "https://canyoublockit.com/extreme-test/"}'

    _build_and_run_docker()

    response = requests.request(
        "POST", url, headers=DOCKER_TEST_HEADERS, data=payload, timeout=60
    )

    try:
        data = json.loads(response.text)
        is_json = True
    except JSONDecodeError:
        data = {}
        is_json = False
    has_url = "url" in data.keys()
    has_meta = "url" in data.keys()
    needs_less_than_a_minute = data["time_until_complete"] < 60

    has_no_exceptions = data["exception"] is None

    # sometimes 13, sometimes 14
    has_expected_advertisment_values = (
        len(data["meta"]["advertisement"]["values"]) > 10
    )
    has_expected_advertisment_decision = (
        data["meta"]["advertisement"]["decision"] is True
    )

    has_expected_easy_privacy_values = (
        len(data["meta"]["easy_privacy"]["values"]) > 10
    )
    has_expected_easy_privacy_decision = (
        data["meta"]["easy_privacy"]["decision"] is True
    )

    has_expected_malicious_extensions_values = (
        len(data["meta"]["malicious_extensions"]["values"]) == 0
    )
    has_expected_malicious_extensions_decision = (
        data["meta"]["malicious_extensions"]["decision"] is False
    )

    has_expected_cookies_in_html_values = (
        len(data["meta"]["cookies_in_html"]["values"]) >= 1
    )
    has_expected_cookies_in_html_decision = (
        data["meta"]["cookies_in_html"]["decision"] is True
    )
    has_expected_fanboy_annoyance_values = (
        len(data["meta"]["fanboy_annoyance"]["values"]) >= 10
    )
    has_expected_fanboy_annoyance_decision = (
        data["meta"]["fanboy_annoyance"]["decision"] is True
    )
    has_expected_easylist_adult_values = (
        len(data["meta"]["easylist_adult"]["values"]) == 2
    )
    has_expected_easylist_adult_decision = (
        data["meta"]["easylist_adult"]["decision"] is True
    )

    has_expected_pop_up_values = len(data["meta"]["pop_up"]["values"]) == 2
    has_expected_pop_up_decision = data["meta"]["pop_up"]["decision"] is True

    has_expected_accessibility_values = data["meta"]["accessibility"][
        "values"
    ] == [0.98, 0.98]
    has_expected_accessibility_decision = (
        data["meta"]["accessibility"]["decision"] is True
    )

    has_expected_g_d_p_r_values = len(data["meta"]["g_d_p_r"]["values"]) == 7
    has_expected_g_d_p_r_decision = (
        data["meta"]["g_d_p_r"]["decision"] is False
    )

    has_expected_javascript_values = (
        len(data["meta"]["javascript"]["values"]) > 10
    )
    has_expected_javascript_decision = (
        data["meta"]["javascript"]["decision"] is True
    )

    has_expected_cookies_values = len(data["meta"]["cookies"]["values"]) > 10
    has_expected_cookies_decision = data["meta"]["cookies"]["decision"] is True

    assert (
        is_json
        and has_url
        and has_meta
        and needs_less_than_a_minute
        and has_no_exceptions
        and has_expected_advertisment_values
        and has_expected_advertisment_decision
        and has_expected_easy_privacy_values
        and has_expected_easy_privacy_decision
        and has_expected_malicious_extensions_values
        and has_expected_malicious_extensions_decision
        and has_expected_cookies_in_html_values
        and has_expected_cookies_in_html_decision
        and has_expected_fanboy_annoyance_values
        and has_expected_fanboy_annoyance_decision
        and has_expected_easylist_adult_values
        and has_expected_easylist_adult_decision
        and has_expected_pop_up_values
        and has_expected_pop_up_decision
        and has_expected_accessibility_values
        and has_expected_accessibility_decision
        and has_expected_g_d_p_r_values
        and has_expected_g_d_p_r_decision
        and has_expected_javascript_values
        and has_expected_javascript_decision
        and has_expected_cookies_values
        and has_expected_cookies_decision
    )
