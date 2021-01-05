import asyncio
import os
import time
from urllib.parse import urlparse

from features.extract_from_files import ExtractFromFiles
from features.html_based import (
    Advertisement,
    CookiesInHtml,
    EasylistAdult,
    EasyPrivacy,
    Paywalls,
)
from features.malicious_extensions import MaliciousExtensions
from features.website_manager import WebsiteManager
from lib.constants import VALUES
from lib.logger import create_logger


def _test_feature(feature_class, html, expectation) -> tuple[bool, bool]:
    _logger = create_logger()

    feature = feature_class(_logger)

    feature.setup()
    website_manager = WebsiteManager.get_instance()

    website_manager.load_raw_data(html)

    if feature.call_async:
        data = asyncio.run(feature.astart())
    else:
        data = feature.start()

    website_manager.reset()

    are_values_correct = set(data[feature.key]["values"]) == set(
        expectation[feature.key]["values"]
    )
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
        "html": "<script src='/xlayer/layer.php?uid='></script>",
        "har": "",
        "url": "",
        "headers": "{}",
    }
    expected = {
        feature.key: {
            "values": ["/xlayer/layer.php?uid=$script"],
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


# TODO: Currently, no solution to find these manually
def test_easylist_adult():
    feature = EasylistAdult
    feature._create_key(feature)
    html = {
        "html": "adlook.net\nver-pelis.net\n,geobanner.fuckbookhookups.com\n 22pixx.xyz \n trkinator.com \n soonbigo",
        "har": "",
        "url": "",
        "headers": "{}",
    }
    expected = {
        feature.key: {
            "values": [],
            "runs_within": 10,  # time the evaluation may take AT MAX -> acceptance test}
        }
    }

    are_values_correct, runs_fast_enough = _test_feature(
        feature_class=feature, html=html, expectation=expected
    )
    assert are_values_correct and runs_fast_enough


def test_cookies_in_html():
    feature = CookiesInHtml
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
            "values": ["||iubenda.com^$third-party"],
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
                "||googletagmanager.com^$image,third-party",
                "||steadfastsystem.com^$third-party",
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
            "values": [".exe", ".pdf", ".js"],
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
    #
    # <a href=\"https://dll-production.s3-de-central.profitbricks.com/media/filer_public/06/78/0678543a-fa24-4aa4-9250-e6a8d7650fd3/arbeitsblatt_analog_losung.pdf\" target=\"_blank\">
    # Arbeitsblatt analog L\u00f6sung.pdf</a>
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
