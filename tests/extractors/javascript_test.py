import pytest

from features.javascript import Javascript
from tests.integration.features_integration_test import mock_website_data


@pytest.mark.asyncio
async def test_javascript(executor):
    feature = Javascript()
    await feature.setup()

    html = """
           <script src='/xlayer/layer.php?uid='></script>
           <script href='some_test_javascript.js'></script>
           """
    site = await mock_website_data(html=html)
    stars, explanation, matches = await feature.extract(site, executor=executor)
    assert matches == {"/xlayer/layer.php?uid="}
