import json
from json import JSONDecodeError

import pytest
import requests

from lib.settings import SKIP_E2E_TESTS
from tests.test_libs import DOCKER_TEST_HEADERS, DOCKER_TEST_URL, _build_and_run_docker


@pytest.mark.skipif(
    SKIP_E2E_TESTS,
    reason="""
    This test takes a lot of time, depending on payload etc - 90s are possible (on 20210105
    Furthermore, it is not idempotent, because it depends on internet resources.
    Sometimes it time outs or data changes - simply because of internet traffic or changes in the websites used.
    Execute it manually and investigate in detail.
    """,
)
def test_e2e():
    url = DOCKER_TEST_URL + "extract_meta"

    payload = '{"url": "https://canyoublockit.com/extreme-test/"}'

    _build_and_run_docker()

    response = requests.request("POST", url, headers=DOCKER_TEST_HEADERS, data=payload, timeout=60)

    try:
        data = json.loads(response.text)
        is_json = True
    except JSONDecodeError:
        data = {}
        is_json = False
    has_url = "url" in data.keys()
    has_meta = "url" in data.keys()
    needs_less_than_a_minute = data["time_until_complete"] < 60

    assert is_json
    assert has_url
    assert has_meta
    assert needs_less_than_a_minute

    has_no_exceptions = data["exception"] is None
    assert has_no_exceptions

    # sometimes 13, sometimes 14
    has_expected_advertisment_values = len(data["meta"]["advertisement"]["values"]) > 10
    has_expected_advertisment_decision = data["meta"]["advertisement"]["isHappyCase"] is True
    assert has_expected_advertisment_values
    assert has_expected_advertisment_decision

    has_expected_easy_privacy_values = len(data["meta"]["easy_privacy"]["values"]) > 6
    has_expected_easy_privacy_decision = data["meta"]["easy_privacy"]["isHappyCase"] is True
    assert has_expected_easy_privacy_values
    assert has_expected_easy_privacy_decision

    has_expected_malicious_extensions_values = len(data["meta"]["malicious_extensions"]["values"]) == 2
    has_expected_malicious_extensions_decision = data["meta"]["malicious_extensions"]["isHappyCase"] is True
    assert has_expected_malicious_extensions_values
    assert has_expected_malicious_extensions_decision

    has_expected_cookies_in_html_values = len(data["meta"]["cookies_in_html"]["values"]) >= 1
    has_expected_cookies_in_html_decision = data["meta"]["cookies_in_html"]["isHappyCase"] is True
    assert has_expected_cookies_in_html_values
    assert has_expected_cookies_in_html_decision

    has_expected_fanboy_annoyance_values = len(data["meta"]["fanboy_annoyance"]["values"]) >= 10
    has_expected_fanboy_annoyance_decision = data["meta"]["fanboy_annoyance"]["isHappyCase"] is True
    assert has_expected_fanboy_annoyance_values
    assert has_expected_fanboy_annoyance_decision

    has_expected_easylist_adult_values = len(data["meta"]["easylist_adult"]["values"]) == 2
    has_expected_easylist_adult_decision = data["meta"]["easylist_adult"]["isHappyCase"] is True
    assert has_expected_easylist_adult_values
    assert has_expected_easylist_adult_decision

    has_expected_pop_up_values = len(data["meta"]["pop_up"]["values"]) == 2
    has_expected_pop_up_decision = data["meta"]["pop_up"]["isHappyCase"] is True
    assert has_expected_pop_up_values
    assert has_expected_pop_up_decision

    has_expected_accessibility_values = data["meta"]["accessibility"]["values"] == [0.98, 0.98]
    has_expected_accessibility_decision = data["meta"]["accessibility"]["isHappyCase"] is True
    assert has_expected_accessibility_values
    assert has_expected_accessibility_decision

    has_expected_g_d_p_r_values = len(data["meta"]["g_d_p_r"]["values"]) >= 7
    has_expected_g_d_p_r_decision = data["meta"]["g_d_p_r"]["isHappyCase"] is False
    assert has_expected_g_d_p_r_values
    assert has_expected_g_d_p_r_decision

    has_expected_javascript_values = len(data["meta"]["javascript"]["values"]) > 10
    has_expected_javascript_decision = data["meta"]["javascript"]["isHappyCase"] is True
    assert has_expected_javascript_values
    assert has_expected_javascript_decision

    has_expected_cookies_values = len(data["meta"]["cookies"]["values"]) > 10
    has_expected_cookies_decision = data["meta"]["cookies"]["isHappyCase"] is True
    assert has_expected_cookies_values
    assert has_expected_cookies_decision
