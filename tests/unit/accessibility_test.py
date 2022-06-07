from unittest import mock

import pytest

from app.models import StarCase
from features.accessibility import Accessibility


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
def test_decide(score, expected_decision):
    accessibility = Accessibility()

    decision, explanation = accessibility._decide(website_data=mock.Mock(score=score))

    assert decision == expected_decision
