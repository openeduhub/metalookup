from unittest import mock

import pytest

from app.models import StarCase
from features.accessibility import Accessibility, AccessibilityScores


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "score, expected_decision",
    [
        (0.98, StarCase.FIVE),
        (0.94, StarCase.FOUR),
        (0.86, StarCase.THREE),
        (0.82, StarCase.TWO),
        (0.75, StarCase.ONE),
        (0.5, StarCase.ZERO),
    ],
)
async def test_extract(score, expected_decision, executor):
    accessibility = Accessibility()

    async def accessibility_api_call_mock(self, url, session, strategy) -> float:  # noqa
        if strategy == "desktop":
            return score + 0.01
        elif strategy == "mobile":
            return score - 0.01
        raise ValueError(f"Invalid strategy {strategy}")

    # intercept the request to the non-running splash and lighthouse container
    # and instead use the checked in response json and a hardcoded score value
    with mock.patch("features.accessibility.Accessibility._execute_api_call", accessibility_api_call_mock):
        decision, explanation, extra = await accessibility.extract(site=mock.Mock(url="url"), executor=executor)

        assert decision == expected_decision
        assert isinstance(extra, AccessibilityScores)
        assert extra.mobile_score == score - 0.01
        assert extra.desktop_score == score + 0.01
        assert extra.average_score == score
