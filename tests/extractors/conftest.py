from typing import Optional, Union
from unittest.mock import Mock

from playwright.async_api import Cookie
from pydantic import HttpUrl

from metalookup.core.content import Content


def mock_content(
    html: Optional[str] = None,
    url: Optional[Union[str, HttpUrl]] = None,
    header: Optional[dict[str, str]] = None,
    cookies: Optional[list[Cookie]] = None,
) -> Content:

    if header is not None:
        # convert to lower case keys to be in line with playwright handling.
        header = {k.lower(): v for k, v in header.items()}

    content = Content(url=url or "https://forums.news.cnn.com/")
    content._cookies = cookies or []
    content._headers = header or {}
    content._html = html or "<html></html>"
    content._response = Mock(status=200, text=Mock(return_value=html), headers=header or {})

    return content
