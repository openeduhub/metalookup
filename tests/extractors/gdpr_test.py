import pytest

from metalookup.features.gdpr import GDPR
from metalookup.lib.tools import runtime
from tests.extractors.conftest import mock_content


@pytest.mark.asyncio
async def test_gdpr(executor):
    feature = GDPR()
    await feature.setup()

    html = """
            <link rel=\"preload\" href=\"/mediathek/podcast/dist/runtime.2e1c836.js\" as=\"script\">
            @font-face {font-family: "Astra";
            src: url(https://canyoublockit.com/wp-content/themes/astra/assets/fonts/astra.svg#astra)
            format("svg");font-weight: normal;font-style: normal;font-display: fallback;}
            <button type='button' class='menu-toggle main-header-menu-toggle  ast-mobile-menu-buttons-fill '
                    aria-controls='primary-menu' aria-expanded='false'>
            <datetime type='datetime'>
            <a href=\"/impressum\">Impressum</a>
            """

    url = "https://www.tutory.de"
    header = {
        "Referrer-Policy": "no-referrer",
        "Strict-Transport-Security": "max-age=15724800; includeSubDomains; preload",
    }
    content = mock_content(html=html, url=url, header=header)  # noqa

    with runtime() as t:
        stars, explanation, values = await feature.extract(content, executor=executor)
    assert t() < 2
    assert values == {
        "preload",
        "https_in_url",
        "hsts",
        "includesubdomains",
        "max_age",
        "found_fonts,https://canyoublockit.com/wp-content/themes/astra/assets/fonts/astra.svg#astra",
        "no-referrer",
        "found_inputs,button,datetime",
        "impressum",
    }
