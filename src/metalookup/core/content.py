import asyncio
import logging
import re
from asyncio import Task
from typing import Optional

from bs4 import BeautifulSoup
from fastapi import HTTPException
from playwright.async_api import Cookie, Request, Response, async_playwright
from pydantic import HttpUrl
from tldextract.tldextract import TLDExtract

from metalookup.lib.settings import PLAYWRIGHT_PAGE_LOAD_TIMEOUT, PLAYWRIGHT_WS_ENDPOINT
from metalookup.lib.tools import get_unique_list, runtime

logger = logging.getLogger(__file__)

_SCRIPT = "script"


class Content:
    """
    The main access point to the content for the different Extractor classes.

    This class provides access to the rendered DOM, the involved http requests and cookies of a URL.

    All features are exposed via async functions, that lazily fetch the content via playwright once accessed. Hence,
    different Extractors can access the features concurrently and independently, but the caching of the features will
    prevent unnecessary overhead.
    """

    tld_extractor: TLDExtract = TLDExtract(cache_dir=None)

    def __init__(self, url: HttpUrl):
        self.url = url
        self._task: Optional[Task] = None
        self._domain: Optional[str] = None
        self._soup: Optional[BeautifulSoup] = None
        self._responses: Optional[list[Response]] = None
        self._requests: Optional[list[Request]] = None
        self._response: Optional[Response] = None
        self._html: Optional[str] = None
        self._cookies: Optional[list[Cookie]] = None

    async def _fetch(self):
        # A pretty primitive implementation of "request deduplication".
        # If fetch is called, we check if there is already a coroutine waiting
        # for fetch to be completed.
        # - If so, we simply await the same task the other coroutine is waiting for
        #   instead of  issuing a new one (that's why tasks are used - instead of plain
        #   awaitables - one can await a task multiple times).
        # - If not, then a new respective task is created and waited for.

        async def _task():
            with runtime() as t:
                async with async_playwright() as p:
                    self._responses = []
                    self._requests = []
                    browser = await p.chromium.connect_over_cdp(endpoint_url=PLAYWRIGHT_WS_ENDPOINT)
                    page = await browser.new_page()

                    # Fixme: we need to await the all_headers in the callbacks, probably because we leak the response
                    #        out of the async_playwright context and it seems we cannot access the all_headers after the
                    #        async_playwright context is closed.
                    #        Eventually turn the content class into a context, i.e. keep the async_context open as long
                    #        as the content class is in use!

                    async def on_request(request: Request):
                        self._requests.append(request)
                        await request.all_headers()

                    async def on_response(response: Response):
                        self._responses.append(response)
                        await response.all_headers()

                    page.on("request", on_request)
                    page.on("response", on_response)

                    # waits for page to fully load (= no network traffic for 500ms) or a max timeout
                    self._response = await page.goto(
                        self.url, wait_until="networkidle", timeout=PLAYWRIGHT_PAGE_LOAD_TIMEOUT * 1000
                    )
                    self._html = await page.content()

                    # playwright offers the cookies in three different ways:
                    #  - via the cookies of the context
                    #  - via the all_header() dictionary where cookies are merged into one "set-cookie" header where
                    #    individual cookies are separated via newlines.
                    #  - via the headers_array() list where the cookies will be separated into individual entries.
                    # Using page.context.cookies() avoids a lot of hassle:
                    #  - no need to parse the new line separated all_headers content.
                    #  - no need to deduplicate (e.g. multiple request may set the same cookie)
                    #  - no need to validate and parse individual cookies
                    self._cookies = await page.context.cookies()
            logger.info(f"Fetched {self.url} in {t():5.2f}s")

        if self._task is None:
            self._task = asyncio.create_task(_task(), name=self.url)

        await self._task

    async def cookies(self) -> list[Cookie]:
        """
        All cookies that will be defined after the communication with the server is completed.
        """

        if self._cookies is None:
            await self._fetch()
        return self._cookies

    async def request(self) -> Request:
        """
        The request for the primary resource.
        - Redirects will be resolved.
        """
        return (await self.response()).request

    async def response(self) -> Response:
        """
        The response of the primary resource.
        """
        if self._response is None:
            await self._fetch()
        return self._response

    async def responses(self) -> list[Response]:
        if self._responses is None:
            await self._fetch()
        return self._responses

    async def requests(self) -> list[Request]:
        if self._requests is None:
            await self._fetch()
        return self._requests

    async def headers(self) -> dict[str, str]:
        """
        The response headers of the main response.
        Playwright docstring:
        > An object with the response HTTP headers. The header names are lower-cased. Note that this method does not
        > return security-related headers, including cookie-related ones. You can use `response.all_headers()` for
        > complete list of headers that include `cookie` information.
        """
        return (await self.response()).headers

    async def html(self) -> str:
        """
        The fulltext HTML-DOM as rendered by playwright.
        Getting the HTML may raise an HTTPException with code:
         - 502 if the server responded with anything but a 200
         - 400 if the response type of the content is not HTML (e.g. when loading a jpg, or pdf).
        """
        if self._html is None:
            await self._fetch()

        response = await self.response()
        # Make sure no meta information is extracted from a 404 placeholder site or similar.
        # Raises an HTTPException which is meant to bubble up to an actual user of the service.
        # To do so, we need to find the HAR entry where the actual content is requested (and skip redirects or
        # other sider requests (e.g. from trackers).
        if response.status != 200:
            raise HTTPException(status_code=502, detail=f"Resource could not be loaded (reported: {response.status})")

        if "text/html" not in (
            content_type := response.headers.get("content-type", "text/html").lower()
        ):  # assume text/html content type as default
            raise HTTPException(
                status_code=400, detail=f"URL {self.url} points to non-html content (Content-Type: {content_type}."
            )

        return self._html

    async def domain(self) -> str:
        if self._domain is None:
            host = self.tld_extractor(url=self.url.replace("http://", "").replace("https://", ""))
            domain = [host.subdomain, host.domain, host.suffix]
            self._domain = ".".join([element for element in domain if element != ""])
        return self._domain

    async def soup(self) -> BeautifulSoup:
        if self._soup is None:
            self._soup = BeautifulSoup(await self.html(), "lxml")
        return self._soup
