import pytest

from metalookup.app.models import StarCase
from metalookup.features.security import Security
from tests.extractors.conftest import mock_content


@pytest.mark.asyncio
async def test_extract(executor):
    feature = Security()
    await feature.setup()

    content = mock_content(
        header={
            "x-frame-options": "sameorigin",
            "content-security-policy": "same_origin",
            "x-xss-protection": "1;mode=block",
            "strict-transport-security": "max-age=15768000;includeSubDomains",
            "referrer-policy": "unsafe-url",
        }
    )
    stars, explanation, failed = await feature.extract(content, executor=executor)
    assert failed == {"x-content-type-options", "cache-control"}
    assert stars == StarCase.ZERO

    content = mock_content(
        header={
            "content-security-policy": "something",
            "referrer-policy": "something",
            "cache-control": "no-cache",
            "x-content-type-options": "nosniff",
            "x-frame-options": "sameorigin",
            "x-xss-protection": "1;mode=block",
            "strict-transport-security": "max-age=15768000;includeSubDomains",
        }
    )
    stars, explanation, failed = await feature.extract(content, executor=executor)
    assert stars == StarCase.FIVE
    assert failed == set()

    content = mock_content(
        header={
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
    stars, explanation, failed = await feature.extract(content, executor=executor)
    assert failed == {"referrer-policy"}
    assert stars == StarCase.ZERO
