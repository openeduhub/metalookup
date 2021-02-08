import json
import os

from features.security import Security
from features.website_manager import WebsiteData
from lib.logger import create_logger

if "PRE_COMMIT" in os.environ:
    from integration.features_integration_test import _test_feature
else:
    from tests.integration.features_integration_test import _test_feature

security_tags = {
    "x-frame-options": ["same_origin"],
    "content-security-policy": ["same_origin"],
    "x-xss-protection": ["1,mode=block"],
    "strict-transport-security": ["max-age=15768000"],
}


def test_start():
    feature = Security
    feature._create_key(feature)

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
    _logger = create_logger()

    security = Security(_logger)

    website_data = WebsiteData()
    website_data.values = [
        "x-frame-options",
        "content-security-policy",
        "vary",
        "x-xss-protection",
    ]
    expected_decision = True
    expected_probability = 1.0

    security.expected_headers = security_tags

    decision, probability = security._decide(website_data=website_data)

    assert probability == expected_probability
    assert decision == expected_decision
