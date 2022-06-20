import abc
import asyncio
import itertools
import os
import re
from concurrent.futures import Executor
from logging import Logger
from typing import Generic, Optional, TypeVar, Union
from urllib.parse import urlparse

from aiohttp import ClientSession

from metalookup.app.models import Explanation, StarCase
from metalookup.core.website_manager import WebsiteData
from metalookup.lib.settings import USE_LOCAL_IF_POSSIBLE

T = TypeVar("T")


class Extractor(Generic[T]):
    key: str  # The name of the extracted metadatum

    @abc.abstractmethod
    async def setup(self):
        """
        Finish initialization of the extractor e.g. by downloading tag lists or other online resources.
        This method must be called for every newly created extractor to fully initialize it.
        """

    @abc.abstractmethod
    async def extract(self, site: WebsiteData, executor: Executor) -> tuple[StarCase, Explanation, T]:
        """
        Extract information from the website returning its star rating, an explanation and additional extractor specific
        information.
        :param site: The content to be analysed.
        :param executor: An executor to which CPU bound processing should be dispatched.
        """


async def download_tag_lists(session: ClientSession, urls: Union[str, list[str]], logger: Logger) -> set[str]:
    """
    Download tags from a list of urls and combine all downloaded tag lists into set removing all duplicates.
    :param session: The client to use for the downloads.
    :param urls: The urls from where to download individual tag lists.
    :param logger: Logger to be used.
    :return: The combined set of all tags.
    """

    def extract_dates(tags: list[str]) -> tuple[Optional[int], Optional[str]]:
        """
        Try to extract the expiration and last modification date from a downloaded tag list.
        :param tags: The individual lines of a downloaded tag list.
        :return: Tuple holding the expiration (in days?) and last modification date.
        """
        expires_expression = re.compile(r"[!#:]\sExpires[:=]\s?(\d+)\s?\w{0,4}")
        last_modified_expression = re.compile(r"[!#]\sLast modified:\s(\d\d\s\w{3}\s\d{4}\s\d\d:\d\d\s\w{3})")
        expiration = None
        last_modification = None
        # sometimes the first couple of lines of the downloaded
        # tag lists contain information about expiration and creation date.
        # checking the first lines would catch them if they are there and in
        # the expected format.
        for line in tags[0:10]:
            if match := last_modified_expression.match(line):
                last_modification = match.group(1)
            elif match := expires_expression.match(line):
                expiration = int(match.group(1))

            if last_modification is not None and expiration is not None:
                break
        return expiration, last_modification

    async def download_tags(url: str) -> tuple[Optional[int], Optional[str], set[str]]:
        taglist_path = "tag_lists/"
        if not os.path.isdir(taglist_path):
            os.makedirs(taglist_path, exist_ok=True)

        filename = os.path.basename(urlparse(url).path)
        if USE_LOCAL_IF_POSSIBLE and os.path.isfile(taglist_path + filename):
            with open(taglist_path + filename, "r") as file:
                tag_list = file.read().splitlines()
        else:
            result = await session.get(url=url)
            if result.status == 200:
                text = await result.text()
                tag_list = text.splitlines()
                if USE_LOCAL_IF_POSSIBLE:
                    with open(taglist_path + filename, "w+") as file:
                        file.write(text)
            else:
                raise RuntimeError(f"Downloading tag list from '{url}' yielded status code '{result.status}'.")

        expiration, last_modification = extract_dates(tag_list)
        logger.info(
            f"Downloaded tag list from {url=} with {len(tag_list)} entries and {expiration=}, {last_modification=}"
        )
        return expiration, last_modification, set(tag_list)

    # normalize urls argument into list[str]
    urls = [urls] if isinstance(urls, str) else urls
    tasks = [download_tags(url=url) for url in urls]
    tags: tuple[tuple[Optional[int], Optional[str], set[str]], ...] = await asyncio.gather(*tasks)
    # return set union, ignore expiration and last modification for now
    return set(itertools.chain(*(t for _, _, t in tags)))
