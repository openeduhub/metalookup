import asyncio
import os
import time
import traceback
from urllib.parse import urlparse

from features.cookies import Cookies
from features.extract_from_files import ExtractFromFiles
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
from features.malicious_extensions import MaliciousExtensions
from features.metatag_explorer import MetatagExplorer
from features.website_manager import WebsiteManager
from lib.constants import VALUES
from lib.logger import get_logger


def _test_feature(feature_class, html, expectation) -> tuple[bool, bool]:
    _logger = get_logger()

    feature = feature_class(_logger)

    feature.setup()

    website_manager: WebsiteManager = WebsiteManager.get_instance()

    website_manager.load_website_data(html)

    try:
        if feature.call_async:
            data = asyncio.run(feature.astart())
        else:
            data = feature.start()
    except Exception as e:
        print("Exception: ", e.args)
        traceback.print_exc()
        data = {}
    finally:
        website_manager.reset()

    are_values_correct = False
    try:
        if data[feature.key]["values"]:
            if isinstance(data[feature.key]["values"][0], dict):
                value_names = [
                    value["name"] for value in data[feature.key]["values"]
                ]
                expected_value_names = [
                    value["name"]
                    for value in expectation[feature.key]["values"]
                ]
                are_values_correct = set(value_names) == set(
                    expected_value_names
                )
            elif isinstance(data[feature.key]["values"][0], list):
                values = [
                    element
                    for value in data[feature.key]["values"]
                    for element in value
                ]
                are_values_correct = set(values) == set(
                    expectation[feature.key]["values"]
                )
            else:
                are_values_correct = set(data[feature.key]["values"]) == set(
                    expectation[feature.key]["values"]
                )
        else:
            are_values_correct = set(data[feature.key]["values"]) == set(
                expectation[feature.key]["values"]
            )
    except TypeError:
        pass

    if are_values_correct and "excluded_values" in expectation[feature.key]:
        are_values_correct = (
            not data[feature.key]["values"]
            in expectation[feature.key]["excluded_values"]
        )

    runs_fast_enough = (
        data[feature.key]["time_required"]
        <= expectation[feature.key]["runs_within"]
    )
    return are_values_correct, runs_fast_enough


def test_advertisement():
    feature = Advertisement
    feature._create_key(feature)
    html = {
        "html": "<script src='/layer.php?bid='></script>",
        "har": "",
        "url": "",
        "headers": "{}",
    }
    expected = {
        feature.key: {
            "values": ["/layer.php?bid="],
            "runs_within": 10,  # time the evaluation may take AT MAX -> acceptance test
        },
    }
    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


def test_paywalls():
    feature = Paywalls
    html = {
        "html": "<paywall></paywalluser>",
        "har": "",
        "url": "",
        "headers": "{}",
    }
    expected = {
        feature.key: {
            "values": ["paywall", "paywalluser"],
            "runs_within": 10,  # time the evaluation may take AT MAX -> acceptance test
        },
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


def test_easylist_adult():
    feature = EasylistAdult
    feature._create_key(feature)
    html = {
        "html": """
<link href='bookofsex.com'/>
<link href='geofamily.ru^$third-party'/>
""",
        "har": "",
        "url": "",
        "headers": "{}",
    }
    expected = {
        feature.key: {
            "values": ["bookofsex.com", "geofamily.ru^$third-party"],
            "runs_within": 10,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


def test_cookies_in_html():
    feature = Cookies
    feature._create_key(feature)
    html = {
        "html": """<div class='ast-small-footer-section ast-small-footer-section-1 ast-small-footer-section-equally ast-col-md-6 ast-col-xs-12' >
Copyright © 2021 Can You Block It<br><a href='https://www.iubenda.com/privacy-policy/24196256'
class='iubenda-black iubenda-embed" title="Privacy Policy ">Privacy Policy</a><script
type="3f8f8d2155875297dce02d6a-text/javascript">(function (w,d) {var loader = function ()
{var s = d.createElement("script"), tag = d.getElementsByTagName("script")[0];
s.src="https://cdn.iubenda.com/iubenda.js"; tag.parentNode.insertBefore(s,tag);};
if(w.addEventListener){w.addEventListener("load", loader, false);}else
if(w.attachEvent){w.attachEvent("onload", loader);}else{w.onload = loader;}})(window, document);
</script><a href="https://canyoublockit.com/disclaimer" rel="nofollow">Disclaimer</a>
<a href="https://www.iubenda.com/privacy-policy/24196256'" rel="nofollow">iubenda</a></div>
    """,
        "har": "",
        "url": "",
        "headers": "{}",
    }
    expected = {
        feature.key: {
            "values": ["https://www.iubenda.com/privacy-policy/24196256"],
            "runs_within": 10,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


def test_easy_privacy():
    feature = EasyPrivacy
    feature._create_key(feature)
    html = {
        "html": """<link rel='dns-prefetch' href='//www.googletagmanager.com' />
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
""",
        "har": "",
        "url": "",
        "headers": "{}",
    }
    expected = {
        feature.key: {
            "values": [
                "//www.googletagmanager.com",
                "https://steadfastsystem.com/v2/0/mhdUYBjmgxDP_SQetgnGiancNmP1JIkDmyyXS_JPnDK2hCg_pE_-EVQw61Zu8YEjN6n_TSzbOSci6fkr2DxbJ4T-NH35ngHIfU1tGluTSrud8VFduwH1nKtjGf3-jvZWHD2MaGeUQ",
            ],
            "excluded_values": [
                "https://cdn.fluidplayer.com/v2/current/fluidplayer.min.js?ver=5.6"
            ],
            "runs_within": 10,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


def test_malicious_extensions():
    feature = MaliciousExtensions
    feature._create_key(feature)
    html = {
        "html": """<a href=\"https://dll-production.s3-de-central.profitbricks.com/media/filer_public/06/78/0678543a-fa24-4aa4-9250-e6a8d7650fd3/arbeitsblatt_analog_losung.pdf\" target=\"_blank\">
Arbeitsblatt analog L\u00f6sung.pdf</a></li><li>
<a href=\"https://dll-production.s3-de-central.profitbricks.com/media/filer_public/32/f6/32f602de-c2df-406b-a678-d8149a84ba9c/arbeitsblatt_analog.pdf\" target=\"_blank\">
Arbeitsblatt analog.pdf</a></li><li>
<a href=\"https://dll-production.s3-de-central.profitbricks.com/media/filer_public/a8/dd/a8dd165c-e432-4355-8144-10312de3ab68/arbeitsblatt_losung.pdf\" target=\"_blank\">
Arbeitsblatt L\u00f6sung.pdf</a></li><li>
<a href=\"https://dll-production.s3-de-central.profitbricks.com/media/filer_public/b0/6c/b06ca365-1001-477a-b85a-9870bfc290f1/arbeitsblatt.pdf\" target=\"_blank\">
Arbeitsblatt.pdf</a></li><li>
<a href=\"https://dll-production.s3-de-central.profitbricks.com/media/filer_public/05/15/051593ca-6338-4950-82d2-30f35cbbb8d7/transparenter_verlauf.pdf\" target=\"_blank\">
Transparenter Verlauf.pdf</a></li><li>
<a href=\"https://dll-production.s3-de-central.profitbricks.com/media/filer_public/d7/fc/d7fc692b-304f-44f9-9215-40091c866bef/vorubung.pdf\" target=\"_blank\">
Vor\u00fcbung.pdf</a></li><li>
<a href=\"https://dll-production.s3-de-central.profitbricks.com/media/filer_public/38/cb/38cbab5e-193e-4014-9e40-3576c0c999da/zusatzmaterial.pdf\" target=\"_blank\">
Zusatzmaterial.pdf</a><li>
<a href=\"https://dll-production.s3-de-central.profitbricks.com/malicious.exe\" target=\"_blank\">
Zusatzmaterial.pdf</a>
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
""",
        "har": "",
        "url": "",
        "headers": "{}",
    }
    expected = {
        feature.key: {
            "values": [".exe", ".pdf"],
            "excluded_values": [".6"],
            "runs_within": 10,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


def _test_extract_from_files_start_wrapper(self):
    before = time.perf_counter()
    website_data = self._prepare_website_data()
    extractable_files = self._get_extractable_files(website_data)

    path = os.getcwd()
    current_dir = path.split("/")[-1]
    if current_dir == "integration":
        path = "/".join(path.split("/")[:-1])
    elif current_dir != "tests":
        path = path + "/tests/"
    path = path + "/files/"

    values = []
    for file in extractable_files:
        filename = os.path.basename(urlparse(file).path)
        extension = filename.split(".")[-1]

        content = {"extracted_content": [], "images": {}}
        if extension == "docx":
            content = self._extract_docx(path + filename)
        elif extension == "pdf":
            content = self._extract_pdfs(path + filename)
        if len(content["extracted_content"]) > 0:
            values.append(filename)
    return {
        self.key: {
            VALUES: values,
            "time_required": time.perf_counter() - before,
        },
    }


def test_extract_from_files():
    feature = ExtractFromFiles
    feature._create_key(feature)
    feature.start = _test_extract_from_files_start_wrapper
    feature.call_async = False

    html = {
        "html": """<a href=\"arbeitsblatt_analog_losung.pdf\" target=\"_blank\">
Arbeitsblatt analog L\u00f6sung.pdf</a>
<a href=\"arbeitsblatt_analog_losung.docx\" target=\"_blank\">
Arbeitsblatt analog L\u00f6sung.docx</a>
""",
        "har": "",
        "url": "",
        "headers": "{}",
    }
    expected = {
        feature.key: {
            "values": [
                "arbeitsblatt_analog_losung.pdf",
                "arbeitsblatt_analog_losung.docx",
            ],
            "excluded_values": [],
            "runs_within": 2,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


def test_fanboy_social_media():
    feature = FanboySocialMedia
    feature._create_key(feature)

    html = {
        "html": """<link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href=
'https://canyoublockit.com/wp-content/plugins/social-icons-widget-by-wpzoom/block/dist/blocks.style.build.css
?ver=1603794146' type='text/css' media='all' />
<script type="4fc846f350e30f875f7efd7a-text/javascript" src=
'https://canyoublockit.com/wp-content/plugins/elementor/assets/lib/share-link/share-link.min.js?ver=3.0.15'
id='share-link-js'></script>
""",
        "har": "",
        "url": "",
        "headers": "{}",
    }
    expected = {
        feature.key: {
            "values": [
                "https://canyoublockit.com/wp-content/plugins/elementor/assets/lib/share-link/share-link.min.js?ver=3.0.15",
                "https://canyoublockit.com/wp-content/plugins/social-icons-widget-by-wpzoom/block/dist/blocks.style.build.css\n?ver=1603794146",
            ],
            "excluded_values": [],
            "runs_within": 2,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


def test_pop_up():
    feature = PopUp
    feature._create_key(feature)

    html = {
        "html": """<noscript><img width="845" height="477"
src="https://canyoublockit.com/wp-content/uploads/2020/01/Screenshot_1.png" class="attachment-large size-large"
alt="Scum Interstitial Ad Placement" loading="lazy" srcset=
"https://canyoublockit.com/wp-content/uploads/2020/01/Screenshot_1.png 845w,
https://canyoublockit.com/wp-content/uploads/2020/01/Screenshot_1-300x169.png 300w,
https://canyoublockit.com/wp-content/uploads/2020/01/Screenshot_1-768x434.png 768w"
sizes="(max-width: 845px) 100vw, 845px" /></noscript>
<div id="KKIbeOcDqZob" class="rIdHlTQAtJaQ" style="background:#dddddd;z-index:9999999; "></div>
<script data-cfasync="false" src="/cdn-cgi/scripts/5c5dd728/cloudflare-static/email-decode.min.js"></script>
<script type="4fc846f350e30f875f7efd7a-text/javascript">/* <![CDATA[ */var anOptions =
{"anOptionChoice":"2","anOptionStats":"1","anOptionAdsSelectors":"","anOptionCookie":"1","anOptionCookieLife":"30",
"anPageRedirect":"","anPermalink":"undefined","anOptionModalEffect":"fadeAndPop","anOptionModalspeed":"350",
"anOptionModalclose":true,"anOptionModalOverlay":"rgba( 0,0,0,0.8 )","anAlternativeActivation":false,
"anAlternativeElement":"","anAlternativeText":","anAlternativeClone":"2","anAlternativeProperties":"",
"anOptionModalShowAfter":0,"anPageMD5":"","anSiteID":0,
"modalHTML":"
""",
        "har": "",
        "url": "",
        "headers": "{}",
    }
    expected = {
        feature.key: {
            "values": [
                "modal",
                "interstitial",
            ],
            "excluded_values": [],
            "runs_within": 2,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


def test_log_in_out():
    feature = LogInOut
    feature._create_key(feature)

    html = {
        "html": """input[type="email"]:focus,input[type="url"]:focus,input[type="password"]:focus,input[type="reset"]:
input#submit,input[type="button"],input[type="submit"],input[type="reset"]
""",
        "har": "",
        "url": "",
        "headers": "{}",
    }
    expected = {
        feature.key: {
            "values": [
                "email",
                "password",
                "submit",
            ],
            "excluded_values": [],
            "runs_within": 2,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


def test_g_d_p_r():
    feature = GDPR
    feature._create_key(feature)

    html = {
        "html": """
<link rel=\"preload\" href=\"/mediathek/podcast/dist/runtime.2e1c836.js\" as=\"script\">
@font-face {font-family: "Astra";
src: url(https://canyoublockit.com/wp-content/themes/astra/assets/fonts/astra.svg#astra)
format("svg");font-weight: normal;font-style: normal;font-display: fallback;}
<button type='button' class='menu-toggle main-header-menu-toggle  ast-mobile-menu-buttons-fill '
        aria-controls='primary-menu' aria-expanded='false'>
<datetime type='datetime'>
<a href=\"/impressum\">Impressum</a>
""",
        "har": "",
        "url": "https://www.tutory.de",
        "headers": '{b"Referrer-Policy": [b"no-referrer"],'
        'b"Strict-Transport-Security": [b"max-age=15724800; includeSubDomains"]}',
    }
    expected = {
        feature.key: {
            "values": [
                "preload",
                "https_in_url",
                "hsts",
                "includesubdomains",
                "do_not_preload",
                "max_age",
                "found_fonts,https://canyoublockit.com/wp-content/themes/astra/assets/fonts/astra.svg#astra",
                "no-referrer",
                "found_inputs,button,datetime",
                "impressum",
            ],
            "excluded_values": ["no_link_rel", "do_not_max_age"],
            "runs_within": 2,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


"""
--------------------------------------------------------------------------------
"""


def test_easylist_germany():
    feature = EasylistGermany
    feature._create_key(feature)

    html = {
        "html": """
<link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/werbung/banner_' type='text/css' media='all' />
<link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='.at/werbung/' type='text/css' media='all' />
<link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='finanzen100.de' type='text/css' media='all' />
""",
        "har": "",
        "url": "",
        "headers": "{}",
    }
    expected = {
        feature.key: {
            "values": [
                "/werbung/banner_",
                ".at/werbung/",
            ],
            "excluded_values": [],
            "runs_within": 2,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


"""
--------------------------------------------------------------------------------
"""


def test_anti_adblock():
    feature = AntiAdBlock
    feature._create_key(feature)

    html = {
        "html": """
<link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/adb_script/' type='text/css' media='all' />
<link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/adbDetect.' type='text/css' media='all' />
<link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='cmath.fr/images/fond2.gif' type='text/css' media='all' />
<link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='||dbz-fantasy.com/ads.css' type='text/css' media='all' />
""",
        "har": "",
        "url": "",
        "headers": "{}",
    }
    expected = {
        feature.key: {
            "values": [
                "cmath.fr/images/fond2.gif",
                "/adb_script/",
                "/adbDetect.",
            ],
            "excluded_values": [],
            "runs_within": 2,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


"""
--------------------------------------------------------------------------------
"""


def test_fanboy_notification():
    feature = FanboyNotification
    feature._create_key(feature)

    html = {
        "html": """
<link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/build/push.js' type='text/css' media='all' />
<link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/notification-ext.' type='text/css' media='all' />
<link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='indianexpress.com' type='text/css' media='all' />
""",
        "har": "",
        "url": "",
        "headers": "{}",
    }
    expected = {
        feature.key: {
            "values": [
                "/build/push.js",
                "/notification-ext.",
            ],
            "excluded_values": [],
            "runs_within": 2,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


"""
--------------------------------------------------------------------------------
"""


def test_fanboy_annoyance():
    feature = FanboyAnnoyance
    feature._create_key(feature)

    html = {
        "html": """
<link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/build/push.js' type='text/css' media='all' />
<link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/notification-ext.' type='text/css' media='all' />
<link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='indianexpress.com' type='text/css' media='all' />
""",
        "har": "",
        "url": "",
        "headers": "{}",
    }
    expected = {
        feature.key: {
            "values": [
                "/build/push.js",
                "/notification-ext.",
            ],
            "excluded_values": [],
            "runs_within": 2,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


"""
--------------------------------------------------------------------------------
"""


def test_reg_wall():
    feature = RegWall
    feature._create_key(feature)

    html = {
        "html": """
<link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='regwall' type='text/css' media='all' />
<link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='registerbtn' type='text/css' media='all' />
""",
        "har": "",
        "url": "",
        "headers": "{}",
    }
    expected = {
        feature.key: {
            "values": ["register", "regwall", "registerbtn"],
            "excluded_values": [],
            "runs_within": 2,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


"""
--------------------------------------------------------------------------------
"""


def test_iframe_embeddable():
    feature = IFrameEmbeddable
    feature._create_key(feature)

    html = {
        "html": "empty_html",
        "har": "",
        "url": "",
        "headers": '{"X-Frame-Options": "deny", "x-frame-options": "same_origin"}',
    }
    expected = {
        feature.key: {
            "values": ["same_origin"],
            "excluded_values": ["deny"],
            "runs_within": 2,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


"""
--------------------------------------------------------------------------------
"""


def test_javascript():
    feature = Javascript
    feature._create_key(feature)

    html = {
        "html": "<script src='/xlayer/layer.php?uid='></script>"
        "<script href='some_test_javascript.js'></script>",
        "har": "",
        "url": "",
        "headers": "",
    }
    expected = {
        feature.key: {
            "values": ["/xlayer/layer.php?uid="],
            "excluded_values": ["some_test_javascript.js"],
            "runs_within": 2,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


"""
--------------------------------------------------------------------------------
"""


def test_cookies():
    feature = Cookies
    feature._create_key(feature)

    html = {
        "html": "empty_html",
        "har": """
{
"log":
    {
    "entries":
    [{
        "response": {"cookies": [{
            "name": "test_response_cookie",
            "httpOnly": false,
            "secure": true}
            ]},
        "request": {"cookies": [{
            "name": "test_request_cookie",
            "httpOnly": false,
            "secure": true}
            ]}
    }]
    }
}""",
        "url": "",
        "headers": "",
    }
    expected = {
        feature.key: {
            "values": [
                {"name": "test_response_cookie"},
                {"name": "test_request_cookie"},
            ],
            "excluded_values": [],
            "runs_within": 2,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


"""
--------------------------------------------------------------------------------
"""


def test_metatag_explorer():
    feature = MetatagExplorer
    feature._create_key(feature)

    html = {
        "html": """
<html lang="en-GB"><head>
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=Edge,chrome=1">
<meta name="description" content="Organmething is in a process.">
<meta name="viewport" content="maximum-scale=1,width=device-width,initial-scale=1,user-scalable=0">
<meta name="apple-itunes-app" content="app-id=461504587"><meta name="slack-app-id" content="A074YH40Z">
<meta name="robots" content="noarchive">
<meta name="referrer" content="origin-when-cross-origin">
</head></html>
""",
        "har": "",
        "url": "",
        "headers": "",
    }
    expected = {
        feature.key: {
            "values": [
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
            ],
            "excluded_values": [],
            "runs_within": 2,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


"""
--------------------------------------------------------------------------------
"""


def test_empty_html():
    feature = MetatagExplorer
    feature._create_key(feature)

    html = {
        "html": "",
        "har": "",
        "url": "",
        "headers": "",
    }
    expected = {
        feature.key: {
            "values": [],
            "excluded_values": [],
            "runs_within": 2,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=None, expectation=expected
    )
    assert are_values_correct and runs_fast_enough
