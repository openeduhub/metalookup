import pytest

from metalookup.app.models import StarCase
from metalookup.features.malicious_extensions import MaliciousExtensions
from tests.extractors.conftest import mock_content


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "expected_values, input_html, expected_decision",
    [
        (
            {".exe"},
            """
            <a href=\"https://some-domain.org/arbeitsblatt_analog_losung.pdf\">Ok</a>
            <a href=\"https://other-domain.com/malicious.foo.exe\">Bad</a>
            """,
            StarCase.ZERO,
        ),
        (
            {".exe"},
            """
            <a href=\"https://some-domain.org/arbeitsblatt_analog_losung.pdf\">Ok</a>
            <a href=\"https://other-domain.com/also-bad.malicious.foo.exe\">Bad</a>
            """,
            StarCase.ZERO,
        ),
        (
            set(),
            "",
            StarCase.FIVE,
        ),
        (
            {".docx", ".pdf"},
            """
            <a href=\"https://other-domain.com/not_really_malicious.docx\">OK</a>
            <a href=\"https://some-domain.com/not_really_malicious.pdf\">OK</a>
            """,
            StarCase.FOUR,
        ),
    ],
)
async def test_malicious_extensions(expected_values, input_html, expected_decision, executor):
    feature = MaliciousExtensions()
    await feature.setup()
    content = mock_content(html=input_html)

    stars, explanation, matches = await feature.extract(content, executor=executor)
    assert matches == expected_values
    assert stars == expected_decision
