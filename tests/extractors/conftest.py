import logging
from typing import Optional

from pydantic import HttpUrl

from metalookup.app.splash_models import HAR, Entry, Header, Log, Request, Response, SplashResponse
from metalookup.core.content import Content


def mock_content(
    html: Optional[str] = None,
    url: Optional[HttpUrl] = None,
    header: Optional[dict[str, str]] = None,
    har: Optional[HAR] = None,
) -> Content:

    if har is not None and header is not None:
        raise ValueError("Cannot provide both har and header!")

    content = Content(
        url=url or "https://forums.news.cnn.com/",
        splash=SplashResponse(
            url=url or "https://forums.news.cnn.com/",
            html=html or "<html></html>",
            har=har
            or HAR(
                log=Log(
                    entries=[
                        Entry(
                            request=Request(
                                headers=[], cookies=[], url=url or "https://forums.news.cnn.com/", method="GET"
                            ),
                            response=Response(
                                headers=[Header(name=k, value=v) for k, v in (header or {}).items()],
                                cookies=[],
                                status=200,
                            ),
                        )
                    ]
                )
            ),
        ),
    )

    return content
