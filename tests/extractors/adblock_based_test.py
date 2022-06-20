import pytest

from metalookup.features.addblock_based import (
    Advertisement,
    AntiAdBlock,
    EasylistAdult,
    EasylistGermany,
    EasyPrivacy,
    FanboyAnnoyance,
    FanboyNotification,
    FanboySocialMedia,
)
from metalookup.lib.tools import runtime
from tests.extractors.conftest import mock_website_data


@pytest.mark.asyncio
async def test_advertisement(executor):
    feature = Advertisement()
    await feature.setup()
    site = await mock_website_data(html="<script src='/layer.php?bid='></script>")

    with runtime() as t:
        stars, explanation, matches = await feature.extract(site, executor=executor)
    assert t() < 10
    assert matches == {"/layer.php?bid="}


@pytest.mark.asyncio
async def test_easylist_adult(executor):
    feature = EasylistAdult()
    await feature.setup()
    html = """
           <link href='bookofsex.com'/>
           <link href='geofamily.ru^$third-party'/>
           """
    site = await mock_website_data(html=html)

    with runtime() as t:
        stars, explanation, matches = await feature.extract(site, executor=executor)

    assert t() < 10
    assert matches == {"bookofsex.com", "geofamily.ru^$third-party"}


@pytest.mark.asyncio
async def test_easy_privacy(executor):
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
    with runtime() as t:
        stars, explanation, matches = await feature.extract(site, executor=executor)
    assert t() < 10
    assert matches == {
        "//www.googletagmanager.com",
        "https://cdn.fluidplayer.com/v2/current/fluidplayer.min.js?ver=5.6",
    }


@pytest.mark.asyncio
async def test_fanboy_social_media(executor):
    feature = FanboySocialMedia()
    await feature.setup()

    html = """
<link rel='stylesheet' id='wpzoom-social-icons-block-style-css' href='https://canyoublockit.com/wp-content/plugins/social-icons-widget-by-wpzoom/block/dist/blocks.style.build.css?ver=1603794146' type='text/css' media='all' />
<script type="4fc846f350e30f875f7efd7a-text/javascript" src='https://canyoublockit.com/wp-content/plugins/elementor/assets/lib/share-link/share-link.min.js?ver=3.0.15' id='share-link-js'></script>
"""
    site = await mock_website_data(html=html)
    with runtime() as t:
        stars, explanation, matches = await feature.extract(site, executor=executor)
    assert t() < 2
    assert matches == {
        "https://canyoublockit.com/wp-content/plugins/elementor/assets/lib/share-link/share-link.min.js?ver=3.0.15",
        "https://canyoublockit.com/wp-content/plugins/social-icons-widget-by-wpzoom/block/dist/blocks.style.build.css?ver=1603794146",
    }


@pytest.mark.asyncio
async def test_easylist_germany(executor):
    feature = EasylistGermany()
    await feature.setup()

    html = """
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/werbung/banner_' type='text/css' media='all' />
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='.at/werbung/' type='text/css' media='all' />
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='finanzen100.de' type='text/css' media='all' />
           """
    site = await mock_website_data(html=html)
    with runtime() as t:
        stars, explanation, matches = await feature.extract(site, executor=executor)
    assert t() < 2
    assert matches == {"/werbung/banner_", ".at/werbung/"}


@pytest.mark.asyncio
async def test_anti_adblock(executor):
    feature = AntiAdBlock()
    await feature.setup()

    html = """
            <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/adb_script/' type='text/css' media='all' />
            <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/adbDetect.' type='text/css' media='all' />
            <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='cmath.fr/images/fond2.gif' type='text/css' media='all' />
            <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='||dbz-fantasy.com/ads.css' type='text/css' media='all' />
            """
    site = await mock_website_data(html=html)
    with runtime() as t:
        stars, explanation, matches = await feature.extract(site, executor=executor)
    assert t() < 2
    assert matches == {"cmath.fr/images/fond2.gif", "/adb_script/", "/adbDetect."}


@pytest.mark.asyncio
async def test_fanboy_notification(executor):
    feature = FanboyNotification()
    await feature.setup()

    html = """
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/build/push.js' type='text/css' media='all' />
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/notification-ext.' type='text/css' media='all' />
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='indianexpress.com' type='text/css' media='all' />
           """
    site = await mock_website_data(html=html)
    with runtime() as t:
        stars, explanation, matches = await feature.extract(site, executor=executor)
    assert t() <= 2
    assert matches == {"/build/push.js", "/notification-ext."}


@pytest.mark.asyncio
async def test_fanboy_annoyance(executor):
    feature = FanboyAnnoyance()
    await feature.setup()

    html = """
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/build/push.js' type='text/css' media='all' />
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/notification-ext.' type='text/css' media='all' />
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='indianexpress.com' type='text/css' media='all' />
           """
    site = await mock_website_data(html=html)
    with runtime() as t:
        stars, explanation, matches = await feature.extract(site, executor=executor)
    assert t() < 2
    assert matches == {"/build/push.js", "/notification-ext."}
