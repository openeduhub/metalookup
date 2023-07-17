import asyncio
import logging
from concurrent.futures import Executor
from logging import Logger
from typing import Optional
from unittest import mock

import adblock
from playwright.sync_api import Request

from metalookup.app.models import Explanation, StarCase
from metalookup.core.content import Content
from metalookup.core.extractor import Extractor, download_tag_lists
from metalookup.lib.tools import runtime

_FOUND_LIST_MATCHES = "Found list matches"
_FOUND_NO_LIST_MATCHES = "Found no list matches"


class AdBlockBasedExtractor(Extractor[set[str]]):
    """
    Base class for features to be extracted with `adblockparser` package.

    The returned extra data corresponds to a sample of the blocked links.
    The sample size can be configured with the limit member variable.

     FIXME: eventually we may want to abandon usage of the adblockparser package all-together and transition
            to a more modern alternative (e.g. the adblock package which is a python wrapper for a native
            rust implementation that would probably speed things up significantly)
    """

    urls: list[str] = []  # needs to be provided by derived class

    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        # playwright request resource types:
        # `document`, `stylesheet`, `image`, `media`, `font`,
        # `script`, `texttrack`, `xhr`, `fetch`, `eventsource`, `websocket`, `manifest`, `other`

        self.adblock_parser_options = {
            "script": True,
            "image": True,
            "stylesheet": True,
            "object": True,
            "xmlhttprequest": True,
            "object-subrequest": True,
            "subdocument": True,
            "document": True,
            "elemhide": True,
            "other": True,
            "background": True,
            "xbl": True,
            "ping": True,
            "dtd": True,
            "media": True,
            "third-party": True,
            "match-case": True,
            "collapse": True,
            "donottrack": True,
            "websocket": True,
            # "domain" key must be populated on use
        }
        self.engine: adblock.Engine = None  # noqa will be initialized in async setup call
        self.limit: Optional[int] = None
        """
        Stop after finding a given amount of to be blocked links.
        For websites with a lot of background requests, this can significantly speed up the extraction process,
        as once it is clear that there will be blocked content, there is no more need to check for more blocked content.
        If set to none, then all requests will be checked.
        """

    async def setup(self) -> None:
        """Fetch tag lists from configured urls."""
        if len(self.urls) == 0:
            raise RuntimeError("Missing url specification of tag lists")
        if self.engine is not None:
            raise RuntimeError("rules must be initialized in async setup call")

        rules = await download_tag_lists(urls=self.urls, logger=self.logger)
        filterset = adblock.FilterSet()
        filterset.add_filters(list(rules))
        self.engine = adblock.Engine(filter_set=filterset)

    def apply_rules(self, domain: str, requests: list[Request]) -> tuple[float, set[str]]:
        """Return the list of matches and the total computation time taken."""
        with runtime() as t:
            values = set()
            for request in requests:
                if self.engine.check_network_urls(
                    url=request.url, source_url=domain, request_type=request.resource_type
                ):
                    values.add(request.url)
                    if self.limit is not None and len(values) > self.limit:
                        break
        return t(), values

    async def extract(self, content: Content, executor: Executor) -> tuple[StarCase, Explanation, set[str]]:
        # fixme: cannot picke self.engine, hence we cannot dispatch the potentially CPU heavy stuff to a different
        #        process
        # loop = asyncio.get_running_loop()
        # duration, values = await loop.run_in_executor(
        #     executor, self.apply_rules, await content.domain(), await content.request()
        # )
        duration, values = self.apply_rules(await content.domain(), await content.requests())
        self.logger.info(
            f"Found {len(values)} links that should be blocked according to ad-block rules in {duration:5.2}s"
        )
        # note: we will never find more than "self.limit" matches
        found_match = len(values) > 0
        explanation = _FOUND_LIST_MATCHES if found_match else _FOUND_NO_LIST_MATCHES
        stars = StarCase.ZERO if found_match else StarCase.FIVE
        return stars, explanation, values


class Advertisement(AdBlockBasedExtractor):
    key = "advertisement"
    urls: list[str] = [
        "https://easylist.to/easylist/easylist.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_adservers.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_adservers_popup.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_allowlist.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_allowlist_dimensions.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_allowlist_general_hide.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_allowlist_popup.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_general_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_general_block_dimensions.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_general_block_popup.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_general_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_specific_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_specific_block_popup.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_specific_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_thirdparty.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_thirdparty_popup.txt",
    ]


class EasyPrivacy(AdBlockBasedExtractor):
    key = "easy_privacy"
    urls: list[str] = [
        "https://easylist.to/easylist/easyprivacy.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easyprivacy/easyprivacy_general.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/easyprivacy/easyprivacy_allowlist.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/easyprivacy/easyprivacy_allowlist_international.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easyprivacy/easyprivacy_specific.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easyprivacy/easyprivacy_specific_international.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easyprivacy/easyprivacy_trackingservers.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easyprivacy/easyprivacy_trackingservers_international.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easyprivacy/easyprivacy_thirdparty.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easyprivacy/easyprivacy_thirdparty_international.txt",
    ]


class FanboyAnnoyance(AdBlockBasedExtractor):
    key = "fanboy_annoyance"
    urls: list[str] = [
        "https://easylist.to/easylist/fanboy-annoyance.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_annoyance_allowlist.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_annoyance_allowlist_general_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_annoyance_general_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_annoyance_general_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_annoyance_international.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_annoyance_specific_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_annoyance_thirdparty.txt",
    ]


class FanboyNotification(AdBlockBasedExtractor):
    key = "fanboy_notification"
    urls: list[str] = [
        # "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_notifications_allowlist.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_notifications_allowlist_general_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_notifications_general_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_notifications_general_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_notifications_specific_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_notifications_specific_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_notifications_thirdparty.txt",
    ]


class FanboySocialMedia(AdBlockBasedExtractor):
    key = "fanboy_social_media"
    urls: list[str] = [
        "https://easylist.to/easylist/fanboy-social.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_social_allowlist.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_social_allowlist_general_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_social_general_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_social_general_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_social_international.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_social_specific_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_social_specific_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_social_thirdparty.txt",
    ]


class AntiAdBlock(AdBlockBasedExtractor):
    key = "anti_adblock"
    urls: list[str] = [
        "https://easylist-downloads.adblockplus.org/antiadblockfilters.txt",
        "https://raw.githubusercontent.com/easylist/antiadblockfilters/master/antiadblockfilters/antiadblock_german.txt",
        "https://raw.githubusercontent.com/easylist/antiadblockfilters/master/antiadblockfilters/antiadblock_english.txt",
    ]


class EasylistGermany(AdBlockBasedExtractor):
    key = "easylist_germany"
    urls: list[str] = [
        "https://easylist.to/easylistgermany/easylistgermany.txt",
        "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_adservers.txt",
        "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_adservers_popup.txt",
        # "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_allowlist.txt",
        # "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_allowlist_dimensions.txt",
        # "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_allowlist_general_hide.txt",
        # "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_allowlist_popup.txt",
        "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_general_block.txt",
        "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_general_block_popup.txt",
        "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_general_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_specific_block.txt",
        "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_specific_block_popup.txt",
        "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_specific_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_thirdparty.txt",
        "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_thirdparty_popup.txt",
    ]


class EasylistAdult(AdBlockBasedExtractor):
    key = "easylist_adult"
    urls: list[str] = [
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_adult/adult_adservers.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_adult/adult_adservers_popup.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/easylist_adult/adult_allowlist.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/easylist_adult/adult_allowlist_popup.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_adult/adult_specific_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_adult/adult_specific_block_popup.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_adult/adult_specific_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_adult/adult_thirdparty.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_adult/adult_thirdparty_popup.txt",
    ]
