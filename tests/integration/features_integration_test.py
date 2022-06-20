import logging
from typing import Optional
from unittest import mock

import pytest
from tldextract.tldextract import ExtractResult, TLDExtract

from app.models import Input
from app.splash_models import HAR, Entry, Header, Log, Request, Response, SplashResponse
from core.website_manager import WebsiteData
from features.gdpr import GDPR


async def mock_website_data(
    html: Optional[str] = None,
    url: Optional[str] = None,
    header: Optional[dict[str, str]] = None,
    har: Optional[HAR] = None,
) -> WebsiteData:

    if har is not None and header is not None:
        raise ValueError("Cannot provide both har and header!")

    mock_extractor = mock.Mock(return_value=ExtractResult(domain="cnn", suffix="com", subdomain="forms.news"))

    url = url or "https://forums.news.cnn.com/"
    html = html or "<html></html>"
    headers = [Header(name=k, value=v) for k, v in (header or {}).items()]
    har = har or HAR(
        log=Log(
            entries=[
                Entry(
                    request=Request(headers=[], cookies=[]),
                    response=Response(headers=headers, cookies=[]),
                )
            ]
        )
    )

    splash_response = SplashResponse(url=url, html=html, har=har)

    return await WebsiteData.from_input(
        Input(url=url, splash_response=splash_response),
        tld_extractor=mock_extractor if url is None else TLDExtract(cache_dir=None),
        logger=logging.getLogger(),
    )


@pytest.mark.asyncio
async def test_g_d_p_r():
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

    site = await mock_website_data(html=html, url=url, header=header)
    duration, values, stars, explanation = await feature.start(site)
    assert duration < 2
    assert set(values) == {
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
    # fixme: what to do with excluded values here?
    #        expected excluded values: "excluded_values": ["no_link_rel", "do_not_max_age"],
