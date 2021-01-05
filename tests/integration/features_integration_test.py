from features.html_based import (
    Advertisement,
    CookiesInHtml,
    EasylistAdult,
    Paywalls,
)
from features.website_manager import WebsiteManager
from lib.logger import create_logger


def _test_feature(feature_class, html, expectation) -> tuple[bool, bool]:
    _logger = create_logger()

    feature = feature_class(_logger)

    feature.setup()
    website_manager = WebsiteManager.get_instance()

    website_manager.load_raw_data(html)

    data = feature.start()

    website_manager.reset()

    are_values_correct = (
        data[feature.key]["values"] == expectation[feature.key]["values"]
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
