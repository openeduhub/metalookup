from unittest import mock

import pytest

from app.models import Explanation, StarCase
from features.accessibility import Accessibility


@pytest.mark.parametrize(
    "score, expected_decision, expected_explanation",
    [
        (
            0.98,
            StarCase.FIVE,
            [Explanation.AccessibilitySuitable],
        ),
        (
            0.94,
            StarCase.FOUR,
            [Explanation.AccessibilitySuitable],
        ),
        (
            0.86,
            StarCase.THREE,
            [Explanation.AccessibilityTooLow],
        ),
        (
            0.82,
            StarCase.TWO,
            [Explanation.AccessibilityTooLow],
        ),
        (
            0.75,
            StarCase.ONE,
            [Explanation.AccessibilityTooLow],
        ),
        (
            0.5,
            StarCase.ZERO,
            [Explanation.AccessibilityTooLow],
        ),
    ],
)
def test_decide(
    score,
    expected_decision,
    expected_explanation,
):
    accessibility = Accessibility()

    decision, explanation = accessibility._decide(website_data=mock.Mock(score=score))

    assert decision == expected_decision
    assert explanation == expected_explanation
