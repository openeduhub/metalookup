import pytest

from features.direct_match import LogInOut, Paywalls, PopUp, RegWall
from lib.tools import runtime
from tests.integration.features_integration_test import mock_website_data


@pytest.mark.asyncio
async def test_paywalls(executor):
    feature = Paywalls()
    await feature.setup()
    site = await mock_website_data(html="<paywall></paywalluser>")

    with runtime() as t:
        stars, explanation, values = await feature.extract(site, executor=executor)

    assert t() < 10
    assert values == {"paywall", "paywalluser"}


@pytest.mark.asyncio
async def test_pop_up(executor):
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
    with runtime() as t:
        stars, explanation, values = await feature.extract(site, executor=executor)
    assert t() < 2
    assert values == {
        "modal",
        "interstitial",
    }


@pytest.mark.asyncio
async def test_log_in_out(executor):
    feature = LogInOut()
    await feature.setup()

    html = """input[type="email"]:focus,input[type="url"]:focus,input[type="password"]:focus,input[type="reset"]:
           input#submit,input[type="button"],input[type="submit"],input[type="reset"]
           """
    site = await mock_website_data(html=html)
    with runtime() as t:
        stars, explanation, values = await feature.extract(site, executor=executor)
    assert t() < 2
    assert values == {
        "email",
        "password",
        "submit",
    }


@pytest.mark.asyncio
async def test_reg_wall(executor):
    feature = RegWall()
    await feature.setup()

    html = """
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='regwall' type='text/css' media='all' />
           <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='registerbtn' type='text/css' media='all' />
           """
    site = await mock_website_data(html=html)
    with runtime() as t:
        stars, explanation, values = await feature.extract(site, executor=executor)
    assert t() < 2
    assert set(values) == {"register", "regwall", "registerbtn"}
