import pytest

from app.models import StarCase
from features.malicious_extensions import MaliciousExtensions
from tests.integration.features_integration_test import mock_website_data


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "expected_values, input_html, expected_decision",
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
async def test_malicious_extensions(
    mocker,
    expected_values,
    input_html,
    expected_decision,
):
    feature = MaliciousExtensions()
    await feature.setup()
    site = mock_website_data(html=input_html)

    duration, values, stars, explanation = await feature.start(site)
    assert duration < 10
    assert set(values) == set(expected_values)
    assert stars == expected_decision
