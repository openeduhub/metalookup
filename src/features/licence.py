import asyncio
from concurrent.futures import Executor
from enum import Enum, auto
from typing import Optional

from pydantic import BaseModel

from app.models import StarCase
from core.extractor import Explanation, Extractor
from core.website_manager import WebsiteData


# see https://docs.python.org/3/library/enum.html#using-automatic-values
# We want the names to show up when serializing and deserializing the enum
class AutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


class Licence(AutoName):
    """
    See https://en.wikipedia.org/wiki/List_of_free-content_licences for more information about the licences.
    """

    CC0 = auto()  # "Creative Commons Zero"
    CC_BY = auto()  # "Creative Commons Attribution"
    CC_BY_SA = auto()  # "Creative Commons Attribution-ShareAlike"
    CC_BY_ND = auto()  # "Creative Commons Attribution-NoDerivatives"
    CC_BY_NC = auto()  # "Creative Commons Attribution-NonCommercial"
    CC_BY_NC_SA = auto()  # "Creative Commons Attribution-NonCommercial-ShareAlike"
    CC_BY_NC_ND = auto()  # "Creative Commons Attribution-NonCommercial-NoDerivatives"
    FREE_BSD = auto()  # "FreeBSD Documentation Licence"
    GFDL = auto()  # "GNU Free Documentation Licence"
    GSFDL = auto()  # "GNU Simpler Free Documentation License"


class DetectedLicences(BaseModel):
    """The additional data that is provided by the licence extractor."""

    # Which licence is guessed (the one with the most counts), or None if no matches were found
    guess: Optional[Licence]
    # How many matches have been found per licence.
    counts: dict[Licence, int]
    # How many matches have been found in total
    total: int

    class Config:
        use_enum_values = True  # make sure that the enum variants are not just numbers


class LicenceExtractor(Extractor[DetectedLicences]):
    """
    Simply searches for matches of the different licence names in the content and counts how many
    matches have been found for each licence.
    """

    key = "licence"

    def __init__(self):
        self.ranking: dict[Licence, StarCase] = {
            # Note: See https://github.com/samuelcolvin/pydantic/issues/1917 for explanation of the .value below
            # least restrictive?
            Licence.CC0.value: StarCase.FIVE,
            Licence.CC_BY.value: StarCase.FIVE,
            Licence.CC_BY_SA.value: StarCase.FIVE,
            # pretty standard and good?
            # fixme: eventually we want to rang CC ND licences lower,
            #  I believe the NoDerivatives means changing is not allowed which might be
            #  less attractive for educational material?
            Licence.CC_BY_ND.value: StarCase.FOUR,
            Licence.CC_BY_NC.value: StarCase.FOUR,
            Licence.CC_BY_NC_SA.value: StarCase.FOUR,
            Licence.CC_BY_NC_ND.value: StarCase.FOUR,
            Licence.FREE_BSD.value: StarCase.FOUR,
            # less well known?
            Licence.GFDL.value: StarCase.THREE,
            Licence.GSFDL.value: StarCase.THREE,
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
