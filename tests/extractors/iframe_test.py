import pytest

from app.models import StarCase
from features.iframe import IFrameEmbeddable
from tests.extractors.conftest import mock_website_data


@pytest.mark.asyncio
async def test_iframe_embeddable(executor):
    feature = IFrameEmbeddable()
    await feature.setup()

    header = {"X-Frame-Options": "DENY", "x-frame-options": "SAMEORIGIN"}

    site = await mock_website_data(header=header)
    stars, explanation, values = await feature.extract(site, executor=executor)
    assert values == {"DENY", "SAMEORIGIN"}
    assert stars is StarCase.ZERO

    header = {"some-header": "some-value"}

    site = await mock_website_data(header=header)
    stars, explanation, values = await feature.extract(site, executor=executor)
    assert values == set()
    assert stars is StarCase.FIVE
