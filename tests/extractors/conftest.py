import logging
from typing import Optional
from unittest import mock

from tldextract.tldextract import ExtractResult, TLDExtract

from metalookup.app.models import Input
from metalookup.app.splash_models import HAR, Entry, Header, Log, Request, Response, SplashResponse
from metalookup.core.website_manager import WebsiteData


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
