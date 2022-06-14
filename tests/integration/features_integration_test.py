import logging
from typing import Optional
from unittest import mock

import pytest
from tldextract.tldextract import ExtractResult, TLDExtract

from app.models import Input
from app.splash_models import HAR, Entry, Header, Log, Request, Response, SplashResponse
from core.website_manager import WebsiteData
from features.gdpr import GDPR
from features.html_based import (
    Advertisement,
    AntiAdBlock,
    EasylistAdult,
    EasylistGermany,
    EasyPrivacy,
    FanboyAnnoyance,
    FanboyNotification,
    FanboySocialMedia,
    IFrameEmbeddable,
    LogInOut,
    Paywalls,
    PopUp,
    RegWall,
)
from features.javascript import Javascript
from features.metatag_explorer import MetatagExplorer


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
async def test_advertisement():
    feature = Advertisement()
    await feature.setup()
    site = await mock_website_data(html="<script src='/layer.php?bid='></script>")

    duration, values, stars, explanation = await feature.start(site)
    assert duration < 10
    assert values == ["/layer.php?bid="]


@pytest.mark.asyncio
async def test_paywalls():
    feature = Paywalls()
    await feature.setup()
    site = await mock_website_data(html="<paywall></paywalluser>")

    duration, values, stars, explanation = await feature.start(site)

    assert duration < 10
    assert values == ["paywall", "paywalluser"]


@pytest.mark.asyncio
async def test_easylist_adult():
    feature = EasylistAdult()
    await feature.setup()
    html = """
           <link href='bookofsex.com'/>
           <link href='geofamily.ru^$third-party'/>
           """
    site = await mock_website_data(html=html)

    duration, values, stars, explanation = await feature.start(site)

    assert duration < 10
    assert values == ["bookofsex.com", "geofamily.ru^$third-party"]


@pytest.mark.asyncio
async def test_easy_privacy():
    feature = EasyPrivacy()
    await feature.setup()
    html = """<link rel='dns-prefetch' href='//www.googletagmanager.com' />
           <script type="6cf3255238f69b4dbff7a6d1-text/javascript">!(function(o,n,t){t=o.createElement(n),
           o=o.getElementsByTagName(n)[0],t.async=1,t.src=
           "https://steadfastsystem.com/v2/0/mhdUYBjmgxDP_SQetgnGiancNmP1JIkDmyyXS_JPnDK2hCg_pE_-EVQw61Zu8YEjN6n_TSzbOSci6fkr2DxbJ4T-NH35ngHIfU1tGluTSrud8VFduwH1nKtjGf3-jvZWHD2MaGeUQ",
           o.parentNode.insertBefore(t,o)})(document,"script"),
           (function(o,n){o[n]=o[n]||function(){(o[n].q=o[n].q||[]).push(arguments)}})(window,"admiral");
           !(function(n,e,r,t){function o(){if((function o(t){try{return(t=localStorage.getItem("v4ac1eiZr0"))&&0<t.split(",")[4]}
           catch(n){}return!1})()){var t=n[e].pubads();typeof t.setTargeting===r&&t.setTargeting("admiral-engaged","true")}}
           (t=n[e]=n[e]||{}).cmd=t.cmd||[],typeof t.pubads===r?o():typeof t.cmd.unshift===r?t.cmd.unshift(o):t.cmd.push(o)})
           (window,"googletag","function");</script><script type="6cf3255238f69b4dbff7a6d1-text/javascript"
           src='https://cdn.fluidplayer.com/v2/current/fluidplayer.min.js?ver=5.6' id='fluid-player-js-js'></script>
           """
    site = await mock_website_data(html=html)
    duration, values, stars, explanation = await feature.start(site)
    assert duration < 10
    assert values == [
        "//www.googletagmanager.com",
        "https://cdn.fluidplayer.com/v2/current/fluidplayer.min.js?ver=5.6",
    ]


@pytest.mark.asyncio
async def test_fanboy_social_media():
    feature = FanboySocialMedia()
    await feature.setup()

    html = """
<link rel='stylesheet' id='wpzoom-social-icons-block-style-css' href='https://canyoublockit.com/wp-content/plugins/social-icons-widget-by-wpzoom/block/dist/blocks.style.build.css?ver=1603794146' type='text/css' media='all' />
<script type="4fc846f350e30f875f7efd7a-text/javascript" src='https://canyoublockit.com/wp-content/plugins/elementor/assets/lib/share-link/share-link.min.js?ver=3.0.15' id='share-link-js'></script>
"""
    site = await mock_website_data(html=html)
    duration, values, stars, explanation = await feature.start(site)
    assert duration < 2
    assert set(values) == {
        "https://canyoublockit.com/wp-content/plugins/elementor/assets/lib/share-link/share-link.min.js?ver=3.0.15",
        "https://canyoublockit.com/wp-content/plugins/social-icons-widget-by-wpzoom/block/dist/blocks.style.build.css?ver=1603794146",
    }


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
async def test_easylist_germany():
    feature = EasylistGermany()
    await feature.setup()

    html = """
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/werbung/banner_' type='text/css' media='all' />
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='.at/werbung/' type='text/css' media='all' />
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='finanzen100.de' type='text/css' media='all' />
           """
    site = await mock_website_data(html=html)
    duration, values, stars, explanation = await feature.start(site)
    assert duration < 2
    assert values == [
        "/werbung/banner_",
        ".at/werbung/",
    ]


"""
--------------------------------------------------------------------------------
"""


@pytest.mark.asyncio
async def test_anti_adblock():
    feature = AntiAdBlock()
    await feature.setup()

    html = """
            <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/adb_script/' type='text/css' media='all' />
            <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/adbDetect.' type='text/css' media='all' />
            <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='cmath.fr/images/fond2.gif' type='text/css' media='all' />
            <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='||dbz-fantasy.com/ads.css' type='text/css' media='all' />
            """
    site = await mock_website_data(html=html)
    duration, values, stars, explanation = await feature.start(site)
    assert duration < 2
    assert set(values) == {
        "cmath.fr/images/fond2.gif",
        "/adb_script/",
        "/adbDetect.",
    }


"""
--------------------------------------------------------------------------------
"""


@pytest.mark.asyncio
async def test_fanboy_notification():
    feature = FanboyNotification()
    await feature.setup()

    html = """
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/build/push.js' type='text/css' media='all' />
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/notification-ext.' type='text/css' media='all' />
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='indianexpress.com' type='text/css' media='all' />
           """
    site = await mock_website_data(html=html)
    duration, values, stars, explanation = await feature.start(site)
    assert duration < 2
    assert values == [
        "/build/push.js",
        "/notification-ext.",
    ]


"""
--------------------------------------------------------------------------------
"""


@pytest.mark.asyncio
async def test_fanboy_annoyance():
    feature = FanboyAnnoyance()
    await feature.setup()

    html = """
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/build/push.js' type='text/css' media='all' />
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/notification-ext.' type='text/css' media='all' />
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='indianexpress.com' type='text/css' media='all' />
           """
    site = await mock_website_data(html=html)
    duration, values, stars, explanation = await feature.start(site)
    assert duration < 2
    assert values == [
        "/build/push.js",
        "/notification-ext.",
    ]


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


"""
--------------------------------------------------------------------------------
"""


@pytest.mark.asyncio
async def test_metatag_explorer():
    feature = MetatagExplorer()
    await feature.setup()

    html = """
            <html lang="en-GB"><head>
            <meta charset="utf-8">
            <meta http-equiv="X-UA-Compatible" content="IE=Edge,chrome=1">
            <meta name="description" content="Organmething is in a process.">
            <meta name="viewport" content="maximum-scale=1,width=device-width,initial-scale=1,user-scalable=0">
            <meta name="apple-itunes-app" content="app-id=461504587"><meta name="slack-app-id" content="A074YH40Z">
            <meta name="robots" content="noarchive">
            <meta name="referrer" content="origin-when-cross-origin">
            </head></html>
            """
    site = await mock_website_data(html=html)
    duration, values, stars, explanation = await feature.start(site)
    assert duration < 2
    assert values == [
        "description",
        "Organmething is in a process.",
        "viewport",
        "maximum-scale=1,width=device-width,initial-scale=1,user-scalable=0",
        "apple-itunes-app",
        "app-id=461504587",
        "slack-app-id",
        "A074YH40Z",
        "robots",
        "noarchive",
        "referrer",
        "origin-when-cross-origin",
    ]
