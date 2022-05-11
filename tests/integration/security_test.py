import json

from app.models import Explanation, StarCase
from core.website_manager import WebsiteData
from features.security import Security
from lib.logger import get_logger
from tests.integration.features_integration_test import _test_feature

security_tags = {
    "x-frame-options": ["same_origin"],
    "content-security-policy": ["same_origin"],
    "x-xss-protection": ["1,mode=block"],
    "strict-transport-security": ["max-age=15768000"],
    "referrer-policy": ["unsafe-url"],
}


def test_start():
    feature = Security

    html = {
        "html": "empty_html",
        "har": "",
        "url": "",
        "headers": json.dumps(security_tags),
    }
    expected = {
        feature.key: {
            "values": [
                "x-frame-options",
                "content-security-policy",
                "x-xss-protection",
                "strict-transport-security",
                "referrer-policy",
            ],
            "excluded_values": [],
            "runs_within": 2,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


"""
--------------------------------------------------------------------------------
"""


def test_decide():
    _logger = get_logger()

    security = Security(_logger)

    website_data = WebsiteData()
    website_data.values = [
        "x-frame-options",
        "content-security-policy",
        "vary",
        "x-xss-protection",
        "referrer-policy",
    ]
    expected_decision = StarCase.FIVE
    expected_explanation = [Explanation.MinimumSecurityRequirementsCovered]

    security.expected_headers = security_tags

    decision, explanation = security._decide(website_data=website_data)

    assert decision == expected_decision
    assert explanation == expected_explanation
