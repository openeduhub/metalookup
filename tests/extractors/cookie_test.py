import json

import pytest

from metalookup.app.splash_models import HAR
from metalookup.features.cookies import Cookies
from tests.extractors.conftest import mock_website_data


@pytest.mark.asyncio
async def test_cookies_har(executor):
    feature = Cookies()
    await feature.setup()

    # make sure that the cookie name partially matches some entries of e.g.
    # https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_general_block.txt
    har = HAR.parse_obj(
        json.loads(
            """{
        "log": {
            "entries": [
                {
                    "response": {
                        "headers": [],
                        "cookies": [
                            {
                                "name": "prefix-cookie-notice.suffix",
                                "value": "dummy",
                                "httpOnly": "false",
                                "secure": "true"
                            }
                        ]
                    },
                    "request": {
                        "headers": [],
                        "cookies": [
                            {
                                "name": "https://some-domain.org/agreements/cookie?key=value",
                                "value": "dummy",
                                "httpOnly": "true",
                                "secure": "false"
                            }
                        ]
                    }
                }
            ]
        }
    }"""
        )
    )
    site = await mock_website_data(har=har)
    stars, explanation, values = await feature.extract(site, executor=executor)

    # extra data returns "cookie-name=cookie-value" pairs for cookies extracted from har
    assert values == {"https://some-domain.org/agreements/cookie?key=value", "prefix-cookie-notice.suffix"}


# FIXME: No clue what this test was supposed to test. Eventually the original request for that website did set some
#        unwanted cookies. But we cannot determine cookies from html content - can we?
# @pytest.mark.asyncio
# async def test_cookies_html(executor):
#     feature = Cookies()
#     await feature.setup()
#     html = """
#            <div class='ast-small-footer-section ast-small-footer-section-1 ast-small-footer-section-equally ast-col-md-6 ast-col-xs-12' >
#            Copyright © 2021 Can You Block It<br><a href='https://www.iubenda.com/privacy-policy/24196256'
#            class='iubenda-black iubenda-embed" title="Privacy Policy ">Privacy Policy</a><script
#            type="3f8f8d2155875297dce02d6a-text/javascript">(function (w,d) {var loader = function ()
#            {var s = d.createElement("script"), tag = d.getElementsByTagName("script")[0];
#            s.src="https://cdn.iubenda.com/iubenda.js"; tag.parentNode.insertBefore(s,tag);};
#            if(w.addEventListener){w.addEventListener("load", loader, false);}else
#            if(w.attachEvent){w.attachEvent("onload", loader);}else{w.onload = loader;}})(window, document);
#            </script><a href="https://canyoublockit.com/disclaimer" rel="nofollow">Disclaimer</a>
#            <a href="https://www.iubenda.com/privacy-policy/24196256'" rel="nofollow">iubenda</a></div>
#            """
#     site = await mock_website_data(html=html)
#     stars, explanation, values = await feature.extract(site, executor)
#     assert values == {"https://www.iubenda.com/privacy-policy/24196256"}
