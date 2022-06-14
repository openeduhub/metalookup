import logging
from typing import Optional
from unittest import mock

import pytest
from tldextract.tldextract import ExtractResult, TLDExtract

from app.models import Input
from app.splash_models import HAR, Entry, Header, Log, Request, Response, SplashResponse
from core.website_manager import WebsiteData
from features.gdpr import GDPR
from features.html_based import IFrameEmbeddable, LogInOut, Paywalls, PopUp, RegWall
from features.javascript import Javascript


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
async def test_paywalls():
    feature = Paywalls()
    await feature.setup()
    site = await mock_website_data(html="<paywall></paywalluser>")

    duration, values, stars, explanation = await feature.start(site)

    assert duration < 10
    assert values == ["paywall", "paywalluser"]


@pytest.mark.asyncio
async def test_pop_up():
    feature = PopUp()
    await feature.setup()

    html = """
<noscript><img width="845" height="477" src="https://canyoublockit.com/wp-content/uploads/2020/01/Screenshot_1.png" class="attachment-large size-large" alt="Scum Interstitial Ad Placement" loading="lazy" srcset="https://canyoublockit.com/wp-content/uploads/2020/01/Screenshot_1.png 845w,https://canyoublockit.com/wp-content/uploads/2020/01/Screenshot_1-300x169.png 300w,https://canyoublockit.com/wp-content/uploads/2020/01/Screenshot_1-768x434.png 768w" sizes="(max-width: 845px) 100vw, 845px" /></noscript>
<div id="KKIbeOcDqZob" class="rIdHlTQAtJaQ" style="background:#dddddd;z-index:9999999; "></div>
<script data-cfasync="false" src="/cdn-cgi/scripts/5c5dd728/cloudflare-static/email-decode.min.js"></script>
<script type="4fc846f350e30f875f7efd7a-text/javascript">/* <![CDATA[ */var anOptions =
{"anOptionChoice":"2","anOptionStats":"1","anOptionAdsSelectors":"","anOptionCookie":"1","anOptionCookieLife":"30",
"anPageRedirect":"","anPermalink":"undefined","anOptionModalEffect":"fadeAndPop","anOptionModalspeed":"350",
"anOptionModalclose":true,"anOptionModalOverlay":"rgba( 0,0,0,0.8 )","anAlternativeActivation":false,
"anAlternativeElement":"","anAlternativeText":","anAlternativeClone":"2","anAlternativeProperties":"",
"anOptionModalShowAfter":0,"anPageMD5":"","anSiteID":0,
"modalHTML":"
"""
    site = await mock_website_data(html=html)
    duration, values, stars, explanation = await feature.start(site)
    assert duration < 2
    assert values == [
        "modal",
        "interstitial",
    ]


@pytest.mark.asyncio
async def test_log_in_out():
    feature = LogInOut()
    await feature.setup()

    html = """input[type="email"]:focus,input[type="url"]:focus,input[type="password"]:focus,input[type="reset"]:
           input#submit,input[type="button"],input[type="submit"],input[type="reset"]
           """
    site = await mock_website_data(html=html)
    duration, values, stars, explanation = await feature.start(site)
    assert duration < 2
    assert values == [
        "email",
        "password",
        "submit",
    ]


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


"""
--------------------------------------------------------------------------------
"""


@pytest.mark.asyncio
async def test_reg_wall():
    feature = RegWall()
    await feature.setup()

    html = """
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='regwall' type='text/css' media='all' />
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='registerbtn' type='text/css' media='all' />
           """
    site = await mock_website_data(html=html)
    duration, values, stars, explanation = await feature.start(site)
    assert duration < 2
    assert set(values) == {"register", "regwall", "registerbtn"}


"""
--------------------------------------------------------------------------------
"""


@pytest.mark.asyncio
async def test_iframe_embeddable():
    feature = IFrameEmbeddable()
    await feature.setup()

    # fixme: This actually tests whether the header normalization in WebsiteData works correctly :-/
    header = {"X-Frame-Options": "deny", "x-frame-options": "same_origin"}
    #
    site = await mock_website_data(header=header)
    duration, values, stars, explanation = await feature.start(site)
    assert duration < 2
    assert values == ["deny;same_origin"]


"""
--------------------------------------------------------------------------------
"""


@pytest.mark.asyncio
async def test_javascript():
    feature = Javascript()
    await feature.setup()

    html = """
           <script src='/xlayer/layer.php?uid='></script>
           <script href='some_test_javascript.js'></script>
           """
    site = await mock_website_data(html=html)
    duration, values, stars, explanation = await feature.start(site)
    assert duration < 2
    assert values == ["/xlayer/layer.php?uid="]
