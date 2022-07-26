import asyncio
import json
import logging
import re
from asyncio import Task
from typing import Optional

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from pydantic import HttpUrl
from tldextract.tldextract import TLDExtract

from metalookup.app.splash_models import HAR, SplashResponse
from metalookup.lib.constants import SCRIPT
from metalookup.lib.settings import SPLASH_HEADERS, SPLASH_TIMEOUT, SPLASH_URL
from metalookup.lib.tools import get_unique_list, runtime

logger = logging.getLogger(__file__)


class Content:
    """
    Enrich the URL of a website with it's html content, HAR, and other features.

    Since the provided features potentially rely on each other, and the html body and HAR are acquired asynchronously,
    all provided features are exposed via async functions. However, under the hood, the instance caches these features
    such that only the first call is potentially expensive.
    This will also allow to move some computation of expensive features into a dedicated process pool to mitigate
    blocking the async runtime for to long.
    """

    tld_extractor: TLDExtract = TLDExtract(cache_dir=None)

    def __init__(self, url: HttpUrl, html: Optional[str] = None, har: Optional[HAR] = None):
        self.url = url
        self._html: Optional[str] = html
        self._har: Optional[HAR] = har
        self._task: Optional[Task[SplashResponse]] = None
        self._domain: Optional[str] = None
        self._soup: Optional[BeautifulSoup] = None
        self._headers: Optional[dict[str, str]] = None
        self._raw_links: Optional[list[str]] = None

    async def _fetch(self) -> tuple[str, HAR]:
        # a pretty primitive implementation of request deduplication.
        # If a request is issued, we check if there is already a request for
        # given URL (self._task).
        # - If so, we simply await the response of that request instead of
        #   issuing a new one (that's why tasks are used - instead of plain
        #   awaitables - one can await a task multiple times).
        # - If not, then a respective task is created.
        assert self._html is None, "Should not fetch when html is already preset"
        assert self._har is None, "Should not fetch when HAR is already preset"

        async def _task() -> SplashResponse:
            async with ClientSession() as session:
                response = await session.get(
                    url=(
                        f"{SPLASH_URL}/render.json?url={self.url}&html={1}&iframes={1}"
                        f"&har={1}&response_body={1}&wait={10}&render_all={1}&script={1}&timeout={SPLASH_TIMEOUT}"
                    ),
                    headers=SPLASH_HEADERS,
                )
                text = await response.text(encoding="UTF-8")
                return SplashResponse.parse_obj(json.loads(text))

        if self._task is None:
            self._task = asyncio.create_task(_task(), name=self.url)
            with runtime() as t:
                response = await self._task
            logger.info(f"Fetched {self.url} from splash in {t():5.2f}s")
        else:
            logger.debug(f"Splash request already in progress, awaiting task {self._task}")
            response = await self._task
        return response.html, response.har

    async def html(self) -> str:
        if self._html is None:
            self._html, self._har = await self._fetch()
        return self._html

    async def har(self) -> HAR:
        if self._har is None:
            self._html, self._har = await self._fetch()
        return self._har

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

    async def headers(self) -> dict[str, str]:
        """A dictionary with the http headers where all keys have been converted to lowercase."""
        # Note: See comment in self.raw_links() about the position of the await statement below.
        har = await self.har()
        if self._headers is None:
            # Splash returns headers as a list of dicts with 'name' and 'value' entries for each header field.
            # Here this list of dicts is transformed into a single dictionary with lowercase header field names.
            # Note: As splash potentially does not normalize duplicate header fields into a comma separate list, we will
            #       normalize them here!
            result = dict()

            # fixme: we just use the first response here which might just be a redirect...
            #        See also https://github.com/openeduhub/metalookup/issues/85
            for header in har.log.entries[0].response.headers:
                lower = header.name.lower()
                if lower not in result:
                    result[lower] = header.value
                else:
                    if result[lower].endswith(";"):
                        result[lower] = result[lower] + header.value
                    else:
                        result[lower] = result[lower] + ";" + header.value
            self._headers = result
        return self._headers

    async def raw_links(self) -> list[str]:
        # Note: The position where we await on the soup is actually critical:
        #       If multiple tasks enter this method, they will all be suspended before the if block.
        #       Once one of the tasks resumes, it will initialize self._raw_links, and once the remaining
        #       tasks resume, they will skip the (expensive) if block. If the await statement would be within
        #       the if block, all tasks would suspend within the if block and hence after resumption would _all_
        #       perform the same rather expensive computation!
        soup = await self.soup()
        if self._raw_links is None:

            def extract_raw_links(soup: BeautifulSoup, image_links: list[str]) -> list[str]:
                source_regex = re.compile(r"src\=[\"|\']([\w\d\:\/\.\-\?\=]+)[\"|\']")
                logger.debug("extracting raw links")
                unique_tags = get_unique_list([tag.name for tag in soup.find_all()])
                logger.debug(f"unique_tags: {unique_tags}")
                if SCRIPT in unique_tags:
                    unique_tags.remove(SCRIPT)
                    source_regex = source_regex.findall
                    script_links = [
                        link
                        for element in soup.find_all(SCRIPT)
                        for link in source_regex(str(element).replace("\n", ""))
                        if link
                    ]
                else:
                    script_links = []

                attributes = [
                    "href",
                    "src",
                    "srcset",
                    "img src",
                    "data-src",
                    "data-srcset",
                ]
                links = [
                    element.attrs.get(attribute)
                    for tag in unique_tags
                    for element in get_unique_list(soup.find_all(tag))
                    for attribute in attributes
                    if element.has_attr(attribute)
                ]
                logger.debug(f"Found {len(links)} links")
                return get_unique_list(links + [el for el in image_links if el is not None] + script_links)

            image_links = [image.attrs.get("src") for image in soup.findAll("img")]
            self._raw_links = extract_raw_links(soup=soup, image_links=image_links)
        return self._raw_links
