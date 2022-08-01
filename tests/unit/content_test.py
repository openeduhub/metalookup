import pytest
from fastapi import HTTPException

from metalookup.core.content import Content


@pytest.mark.asyncio
async def test_content_basic():
    content = Content(url="https://www.google.com")  # noqa
    assert await content.html() != ""
    assert await content.soup() is not None
    assert len(await content.raw_links()) > 0


@pytest.mark.asyncio
async def test_content_redirect():
    content = Content(url="https://google.com")  # noqa
    response = await content.response()
    assert response.request.url == "https://www.google.com/"
    assert response.status == 200


@pytest.mark.asyncio
async def test_content_cookies():
    content = Content(url="https://www.google.com")  # noqa
    cookies = await content.cookies()
    assert len(cookies) > 0
    assert isinstance(cookies, list)
    assert all(all(key in cookie for key in ("name", "value")) for cookie in cookies)


@pytest.mark.asyncio
async def test_non_html_content():
    content = Content(
        url="https://wirlernenonline.de/wp-content/themes/wir-lernen-online/src/assets/img/wlo-logo.svg"  # noqa
    )
    # intercept the request to the non-running lighthouse container and pretend that lighthouse would give an
    # accessibility rating for non html content because we want to test the manager here.
    with pytest.raises(HTTPException) as exception:
        await content.html()
        assert exception.value.status_code == 400
