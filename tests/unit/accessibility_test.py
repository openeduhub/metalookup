import pytest

from features.accessibility import Accessibility

"""
--------------------------------------------------------------------------------
"""


@pytest.mark.parametrize(
    "score_text, status_code, expected_score",
    [
        ("", 200, [-1]),
        ('{"score": 3}', 200, [3]),
    ],
)
def test_accessibility(mocker, score_text, status_code, expected_score):
    Accessibility._logger = mocker.MagicMock()

    score = Accessibility.extract_score(
        Accessibility, score_text=score_text, status_code=status_code
    )
    assert score == expected_score
