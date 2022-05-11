import asyncio

import pytest

from app.models import StarCase
from core.website_manager import WebsiteManager
from features.malicious_extensions import MaliciousExtensions
from lib.constants import STAR_CASE
from lib.logger import get_logger
from tests.integration.features_integration_test import _test_feature


@pytest.mark.parametrize(
    "values, input_html, expected_decision",
    [
        (
            [".exe", ".pdf"],
            """<a href=\"https://dll-production.s3-de-central.profitbricks.com/media/filer_public/06/78/0678543a-fa24-4aa4-9250-e6a8d7650fd3/arbeitsblatt_analog_losung.pdf\" target=\"_blank\">
                Arbeitsblatt analog L\u00f6sung.pdf</a>
                <a href=\"https://dll-production.s3-de-central.profitbricks.com/malicious.exe\" target=\"_blank\">
                Zusatzmaterial.pdf</a>
                """,
            StarCase.ZERO,
        ),
        (
            [],
            "",
            StarCase.FIVE,
        ),
        (
            [".docx", ".pdf"],
            """<a href=\"https://dll-production.s3-de-central.profitbricks.com/not_really_malicious.docx\" target=\"_blank\"></a>
                <a href=\"https://dll-production.s3-de-central.profitbricks.com/not_really_malicious.pdf\" target=\"_blank\">
                Zusatzmaterial.pdf</a>
                """,
            StarCase.FOUR,
        ),
    ],
)
def test_malicious_extensions(
    mocker,
    values,
    input_html,
    expected_decision,
):
    feature = MaliciousExtensions
    html = {
        "html": input_html,
        "har": "",
        "url": "",
        "headers": "{}",
    }
    expected = {
        feature.key: {
            "values": values,
            "star_case": expected_decision,
            "excluded_values": [".6"],
            "runs_within": 10,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough

    feature = feature(get_logger())

    feature.setup()

    website_manager: WebsiteManager = WebsiteManager.get_instance()

    website_manager.load_website_data(html)

    data = asyncio.run(feature.start())
    assert data["malicious_extensions"][STAR_CASE] == expected_decision
    website_manager.reset()
