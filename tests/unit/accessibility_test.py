import pytest

from features.accessibility import Accessibility

"""
--------------------------------------------------------------------------------
"""


@pytest.mark.parametrize(
    "score_text, expected_score",
    [
        ("", -1),
        ('{"score": 3}', 3),
    ],
)
def test_accessibility(mocker, score_text, expected_score):
    Accessibility._logger = mocker.MagicMock()

    score = Accessibility.extract_score(Accessibility, score_text=score_text)
    assert score == expected_score
