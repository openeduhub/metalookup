from unittest import mock

import pytest

from app.models import Explanation, StarCase
from features.security import Security


@pytest.mark.asyncio
async def test_start():
    feature = Security()
    await feature.setup()

    site = mock.Mock(
        headers={
            "x-frame-options": "sameorigin",
            "content-security-policy": "same_origin",
            "x-xss-protection": "1;mode=block",
            "strict-transport-security": "max-age=15768000;includeSubDomains",
            "referrer-policy": "unsafe-url",
        }
    )

    duration, values, stars, explanation = await feature.start(site)
    assert duration < 2
    assert set(values) == {
        "x-frame-options",
        "content-security-policy",
        "x-xss-protection",
        "strict-transport-security",
        "referrer-policy",
    }


@pytest.mark.asyncio
async def test_decide():
    feature = Security()
    await feature.setup()

    duration, values, stars, explanation = await feature.start(
        site=mock.Mock(
            headers={
                "content-security-policy": "something",
                "referrer-policy": "something",
                "cache-control": "no-cache",
                "x-content-type-options": "nosniff",
                "x-frame-options": "sameorigin",
                "x-xss-protection": "1;mode=block",
                "strict-transport-security": "max-age=15768000;includeSubDomains",
            }
        )
    )

    assert stars == StarCase.FIVE
    assert explanation == [Explanation.MinimumSecurityRequirementsCovered]

    duration, values, stars, explanation = await feature.start(
        site=mock.Mock(
            headers={
                "content-security-policy": "something",
                # one header missing -> zero stars
                # "referrer-policy": "something",
                "cache-control": "no-cache",
                "x-content-type-options": "nosniff",
                "x-frame-options": "sameorigin",
                "x-xss-protection": "1;mode=block",
                "strict-transport-security": "max-age=15768000;includeSubDomains",
            }
        )
    )

    assert stars == StarCase.ZERO
    assert explanation == [Explanation.IndicatorsForInsufficientSecurityFound]
