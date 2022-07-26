import pytest

from metalookup.app.models import StarCase
from metalookup.features.iframe import IFrameEmbeddable
from tests.extractors.conftest import mock_content


@pytest.mark.asyncio
async def test_iframe_embeddable(executor):
    feature = IFrameEmbeddable()
    await feature.setup()

    header = {"X-Frame-Options": "DENY", "x-frame-options": "SAMEORIGIN"}

    content = mock_content(header=header)
    stars, explanation, values = await feature.extract(content, executor=executor)
    assert values == {"DENY", "SAMEORIGIN"}
    assert stars is StarCase.ZERO

    header = {"some-header": "some-value"}

    content = mock_content(header=header)
    stars, explanation, values = await feature.extract(content, executor=executor)
    assert values == set()
    assert stars is StarCase.FIVE
