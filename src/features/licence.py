import asyncio
import enum
from concurrent.futures import Executor
from typing import Optional

from pydantic import BaseModel

from app.models import StarCase
from core.extractor import Explanation, Extractor
from core.website_manager import WebsiteData


class Licence(enum.Enum):
    """
    See https://en.wikipedia.org/wiki/List_of_free-content_licences for more information about the licences.
    """

    CC0 = "Creative Commons Zero"
    CC_BY = "Creative Commons Attribution"
    CC_BY_SA = "Creative Commons Attribution-ShareAlike"
    CC_BY_ND = "Creative Commons Attribution-NoDerivatives"
    CC_BY_NC = "Creative Commons Attribution-NonCommercial"
    CC_BY_NC_SA = "Creative Commons Attribution-NonCommercial-ShareAlike"
    CC_BY_NC_ND = "Creative Commons Attribution-NonCommercial-NoDerivatives"
    FREE_BSD = "FreeBSD Documentation Licence"
    GFDL = "GNU Free Documentation Licence"
    GSFDL = "GNU Simpler Free Documentation License"


class DetectedLicences(BaseModel):
    """The additional data that is provided by the licence extractor."""

    # Which licence is guessed (the one with the most counts), or None if no matches were found
    guess: Optional[Licence]
    # How many matches have been found per licence.
    counts: dict[Licence, int]
    # How many matches have been found in total
    total: int


class LicenceExtractor(Extractor[DetectedLicences]):
    """
    Simply searches for matches of the different licence names in the content and counts how many
    matches have been found for each licence.
    """

    key = "licence"

    def __init__(self):
        self.ranking: dict[Licence, StarCase] = {
            # least restrictive?
            Licence.CC0: StarCase.FIVE,
            Licence.CC_BY: StarCase.FIVE,
            Licence.CC_BY_SA: StarCase.FIVE,
            # pretty standard and good?
            # fixme: eventually we want to rang CC ND licences lower,
            #  I believe the NoDerivatives means changing is not allowed which might be
            #  less attractive for educational material?
            Licence.CC_BY_ND: StarCase.FOUR,
            Licence.CC_BY_NC: StarCase.FOUR,
            Licence.CC_BY_NC_SA: StarCase.FOUR,
            Licence.CC_BY_NC_ND: StarCase.FOUR,
            Licence.FREE_BSD: StarCase.FOUR,
            # less well known?
            Licence.GFDL: StarCase.THREE,
            Licence.GSFDL: StarCase.THREE,
        }
        """Defines how we map from a detected licence to a star rating"""

        self.synonyms: dict[Licence, tuple[str, ...]] = {
            Licence.CC0: (
                "CC0",
                "Creative Commons Zero",
            ),
            Licence.CC_BY: (
                "CC BY",
                "Creative Commons Attribution",
            ),
            Licence.CC_BY_SA: (
                "CC BY-SA",
                "Creative Commons Attribution-ShareAlike",
            ),
            Licence.CC_BY_ND: (
                "CC BY-ND",
                "Creative Commons Attribution-NoDerivatives",
            ),
            Licence.CC_BY_NC: (
                "CC BY-NC",
                "Creative Commons Attribution-NonCommercial",
            ),
            Licence.CC_BY_NC_SA: (
                "CC BY-NC-SA",
                "Creative Commons Attribution-NonCommercial-ShareAlike",
            ),
            Licence.CC_BY_NC_ND: (
                "CC BY-NC-ND",
                "Creative Commons Attribution-NonCommercial-NoDerivatives",
            ),
            Licence.FREE_BSD: ("FreeBSD Documentation Licence",),
            Licence.GFDL: ("GNU Free Documentation Licence",),
            Licence.GSFDL: ("GNU Simpler Free Documentation License",),
        }
        """Defines the set of patterns that are taken as a match for given licence"""

    async def setup(self):
        pass  # nothing to do but setup method required by interface

    def result(self, html: str) -> DetectedLicences:
        """
        Use regex parsing to check if any of the licence names show up in the html content.
        """
        counts = {licence: sum(html.count(synonym) for synonym in self.synonyms[licence]) for licence in Licence}

        # with the above code we double count some occurrences (e.g. "CC BY-SA" will be counted as CC-BY and CC-BY-SA)
        # hence, we here subtract all these double counts:
        counts[Licence.CC_BY] -= (
            counts[Licence.CC_BY_SA]
            + counts[Licence.CC_BY_NC]
            + counts[Licence.CC_BY_ND]
            + counts[Licence.CC_BY_NC_ND]
            + counts[Licence.CC_BY_NC_SA]
        )

        counts[Licence.CC_BY_NC] -= counts[Licence.CC_BY_NC_SA] + counts[Licence.CC_BY_NC_ND]

        nonzero = {licence: count for licence, count in counts.items() if count > 0}
        return DetectedLicences(
            counts=nonzero,
            # If there are counts, then take the one with the highest count
            guess=None if len(nonzero) == 0 else sorted(nonzero.items(), key=lambda tpl: tpl[1])[-1][0],
            total=sum(nonzero.values()),
        )

    async def extract(self, site: WebsiteData, executor: Executor) -> tuple[StarCase, Explanation, DetectedLicences]:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(executor, self.result, site.html)
        if result.guess is None:
            return StarCase.ZERO, "Found insufficient matches of any licence strings in content", result
        return (
            self.ranking[result.guess],
            f"Found {result.counts[result.guess]} matches for {result.guess} in content",
            result,
        )
