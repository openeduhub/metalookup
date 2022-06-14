from unittest import mock

import pytest

from app.models import StarCase
from features.security import Security


@pytest.mark.asyncio
async def test_extract(executor):
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
    stars, explanation, failed = await feature.extract(site, executor=executor)
    assert failed == {"x-content-type-options", "cache-control"}
    assert stars == StarCase.ZERO

    site = mock.Mock(
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
    stars, explanation, failed = await feature.extract(site, executor=executor)
    assert stars == StarCase.FIVE
    assert failed == set()

    site = mock.Mock(
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
    stars, explanation, failed = await feature.extract(site, executor=executor)
    assert failed == {"referrer-policy"}
    assert stars == StarCase.ZERO
