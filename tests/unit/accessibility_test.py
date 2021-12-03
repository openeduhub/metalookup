import pytest

from app.models import StarCase, Explanation
from features.accessibility import Accessibility
from features.website_manager import WebsiteData

"""
--------------------------------------------------------------------------------
"""


@pytest.mark.parametrize(
    "score_text, expected_score",
    [
        ("", -1),
        ('{"score": [3]}', 3),
    ],
)
def test_accessibility(mocker, score_text, expected_score):
    Accessibility._logger = mocker.MagicMock()

    score = Accessibility.extract_score(Accessibility, score_text=score_text)
    assert score == expected_score


"""
--------------------------------------------------------------------------------
"""


@pytest.mark.parametrize(
    "values, decision_threshold, expected_decision,  expected_explanation",
    [
        (
                [0.5],
                0,
                StarCase.FIVE,
                [Explanation.AccessibilitySuitable],
        ),
        ([0.5], 0.5, StarCase.ZERO,  [Explanation.AccessibilityTooLow]),
        (
                [0.75, 0.25],
                0.5,
                StarCase.ZERO,
                [Explanation.AccessibilityTooLow],
        ),
        (
                [0.6, 0.8],
                0.5,
                StarCase.FIVE,
                [Explanation.AccessibilitySuitable],
        ),
    ],
)
def test_decide(
    mocker,
    values,
    decision_threshold,
    expected_decision,
    expected_explanation,
):
    website_data = WebsiteData()

    website_data.values = values
    accessibility = Accessibility(mocker.MagicMock())

    accessibility.decision_threshold = decision_threshold

    decision, explanation = accessibility._decide(
        website_data=website_data
    )

    assert decision == expected_decision
    assert explanation == expected_explanation
