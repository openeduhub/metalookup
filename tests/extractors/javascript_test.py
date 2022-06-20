import pytest

from metalookup.features.javascript import Javascript
from tests.extractors.conftest import mock_website_data


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
