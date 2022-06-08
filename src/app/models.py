from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, Field, HttpUrl

from app.splash_models import SplashResponse

Explanation = str


class StarCase(int, Enum):
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5

    def __repr__(self):
        return str(self.value)


class MetadataTags(BaseModel):
    stars: StarCase = Field(
        description="A user friendly decision whether or not the happy case is fulfilled"
        " or whether everything is unclear",
    )
    explanation: Explanation = Field(
        description="A brief explanation to be displayed in the frontend what"
        " reasons the code had for its decision.",
    )
    extra: Optional[Any] = Field(
        description="Extra information provided by the meta data extractor about how it came to its conclusion."
        " Use the .../extract?extra=true query parameter in the endpoint to get this populated."
    )


class Error(BaseModel):
    error: str


class Output(BaseModel):
    url: HttpUrl = Field(..., description="The base url of the scraped website.")

    advertisement: Union[MetadataTags, Error] = Field(
        default=None,
        description="Beta. Are there advertisments?"
        "Probability = "
        "Ratio of found elements which are identified as ads.",
    )
    easy_privacy: Union[MetadataTags, Error] = Field(
        default=None,
        description="Beta. Are there trackers?" "Probability = " "1 If any element is found, else 0",
    )
    malicious_extensions: Union[MetadataTags, Error] = Field(
        default=None,
        description="Beta. Are there malicious extensions, e.g. .exe, .docm?"
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    extract_from_files: Union[MetadataTags, Error] = Field(
        default=None,
        description="Beta. Can all linked files be extracted, "
        "e.g., is the text in a PDF readable?"
        "Probability = "
        "Ratio of found files which are extractable.",
    )
    cookies: Union[MetadataTags, Error] = Field(
        default=None,
        description="Alpha. Are cookies set and are they not whitelisted? "
        "Currently, there is no whitelist, yet."
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    fanboy_annoyance: Union[MetadataTags, Error] = Field(
        default=None,
        description="Beta. Code that indicates 'annoying' behaviour." "Probability = " "Ratio of matching elements.",
    )
    fanboy_notification: Union[MetadataTags, Error] = Field(
        default=None,
        description="Beta. Code that indicates notifications." "Probability = " "Ratio of matching elements.",
    )
    fanboy_social_media: Union[MetadataTags, Error] = Field(
        default=None,
        description="Beta. Code that indicates social media links and content."
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    anti_adblock: Union[MetadataTags, Error] = Field(
        default=None,
        description="Beta. Code that indicates anti adblock walls."
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    easylist_germany: Union[MetadataTags, Error] = Field(
        default=None,
        description="Beta. A blocking list specific for Germany."
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    easylist_adult: Union[MetadataTags, Error] = Field(
        default=None,
        description="Beta. A blocking list specific adult/PG18 content."
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    paywall: Union[MetadataTags, Error] = Field(
        default=None,
        description="Alpha. Keywords indicating paywalls."
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    security: Union[MetadataTags, Error] = Field(
        default=None,
        description="Alpha. Are security policies set? "
        "This feature is currently checking many parameters, which are partially new. "
        "Probability = "
        "Ratio of matching elements.",
    )
    iframe_embeddable: Union[MetadataTags, Error] = Field(
        default=None,
        description="Release. Are iFrames embeddable?" "Probability = " "1 If any matching element is found, else 0.",
    )
    pop_up: Union[MetadataTags, Error] = Field(
        default=None,
        description="Alpha. Are pop ups present?" "Probability = " "1 If any matching element is found, else 0.",
    )
    reg_wall: Union[MetadataTags, Error] = Field(
        default=None,
        description="Alpha. Are registration walls present?"
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    log_in_out: Union[MetadataTags, Error] = Field(
        default=None,
        description="Alpha. Is content present that indicates log in or out forms?"
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    accessibility: Union[MetadataTags, Error] = Field(
        default=None,
        description="Beta. Google Lighthouse based calculation of accessibility"
        "Probability = "
        "1 if the website is 100% accessible, "
        "0 if the website is not accessible at all.",
    )
    g_d_p_r: Union[MetadataTags, Error] = Field(
        default=None,
        description="Alpha. Are there indications that GDPR is obeyed?"
        "Probability = "
        "The more indicators are found the higher this value is.",
    )
    javascript: Union[MetadataTags, Error] = Field(
        default=None,
        description="Alpha. Is there javascript among the files of this website?" "Always False for now",
    )
    metatag_explorer: Union[MetadataTags, Error] = Field(
        default=None,
        description="Alpha. Store meta tags to explore for interesting data"
        "Probability = "
        "Ratio fo javascript files versus all files.",
    )
    licence: Union[MetadataTags, Error] = Field(
        default=None,
        description="Information about the potential licence of the content. Determined by scanning the content for"
        " common licence names.",
    )


class Input(BaseModel):
    url: HttpUrl = Field(..., description="The URL where the content was crawled from.")
    splash_response: Optional[SplashResponse] = Field(
        default=None,
        description="The response object returned from splash when queried with "
        "html=1, iframes=1, har=1, response_body=1, render_all=1, script=1."
        "See https://splash.readthedocs.io/en/stable/api.html#render-html for more information."
        "If omitted, a respective query will be issued to splash internally.",
    )


class Ping(BaseModel):
    status: str = Field(
        default="not ok",
        description="Ping output. Should be 'ok' in happy case.",
    )


class DeleteCacheOutput(BaseModel):
    deleted_rows: int = Field(
        default=-1,
        description="Number of deleted rows from cache. Each row represents one top-level-domain.",
    )


class DeleteCacheInput(BaseModel):
    domain: Optional[str] = Field(default="", description="The host domain to be reset.")
