from dataclasses import dataclass
from typing import Optional

from app.splash_models import SplashResponse


@dataclass(frozen=True)
class Message:  # fixme: should eventually become obsolete and be identical with input model.
    """
    If a message is lacking any of the html, header, or har fields, then the URL will be
    used to issue a request and fetch the content, headers, and har. I.e the response will
    replace any potentially existing content, header, or har with the received response.
    """

    url: str
    """The url of the content to analyze."""
    splash_response: Optional[SplashResponse]
    """
    Optional dictionary resembling the Response format of Splash which must also
    include the har (HTTP Archive format https://en.wikipedia.org/wiki/HAR_(file_format)))
    """
    whitelist: Optional[list[str]]
    """Which extractors (defined by their keys) to use. If none, then all extractors should be used."""
    bypass_cache: bool
    """Whether returning cached data is allowed."""
