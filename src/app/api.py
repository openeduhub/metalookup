import json
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.communication import QueueCommunicator
from lib.constants import (
    DECISION,
    MESSAGE_ALLOW_LIST,
    MESSAGE_EXCEPTION,
    MESSAGE_HAR,
    MESSAGE_HEADERS,
    MESSAGE_HTML,
    MESSAGE_URL,
    PROBABILITY,
    TIME_REQUIRED,
    VALUES,
)
from lib.timing import get_utc_now


class MetadataTags(BaseModel):
    values: list = Field(
        default=[], description="Raw values found by the metadata extractors."
    )
    probability: float = Field(
        default=-1,
        description="The calculated probability that this metadatum is present in the website.",
    )
    decision: bool = Field(
        default=None,
        description="A user friendly decision whether or not this metadatum is present in the website.",
    )
    time_for_completion: Optional[float] = Field(
        default=-1,
        description="Debug information. How long did this metadata take?",
    )


class ListTags(BaseModel):
    advertisement: Optional[bool] = True
    easy_privacy: Optional[bool] = True
    malicious_extensions: Optional[bool] = True
    extracted_links: Optional[bool] = True
    extract_from_files: Optional[bool] = True
    cookies_in_html: Optional[bool] = True
    cookies: Optional[bool] = True
    fanboy_annoyance: Optional[bool] = True
    fanboy_notification: Optional[bool] = True
    fanboy_social_media: Optional[bool] = True
    anti_adblock: Optional[bool] = True
    easylist_germany: Optional[bool] = True
    easylist_adult: Optional[bool] = True
    paywall: Optional[bool] = True
    content_security_policy: Optional[bool] = True
    iframe_embeddable: Optional[bool] = True
    pop_up: Optional[bool] = True
    reg_wall: Optional[bool] = True
    log_in_out: Optional[bool] = True
    accessibility: Optional[bool] = True
    g_d_p_r: Optional[bool] = True
    javascript: Optional[bool] = True


class ExtractorTags(BaseModel):
    advertisement: MetadataTags = Field(
        default=None,
        description="Beta. Are there advertisments?"
        "Probability = "
        "Ratio of found elements which are identified as ads.",
    )
    easy_privacy: MetadataTags = Field(
        default=None,
        description="Beta. Are there trackers?"
        "Probability = "
        "1 If any element is found, else 0",
    )
    malicious_extensions: MetadataTags = Field(
        default=None,
        description="Beta. Are there malicious extensions, e.g. .exe, .docm?"
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    extract_from_files: MetadataTags = Field(
        default=None,
        description="Beta. Can all linked files be extracted, "
        "e.g., is the text in a PDF readable?"
        "Probability = "
        "Ratio of found files which are extractable.",
    )
    cookies_in_html: MetadataTags = Field(
        default=None,
        description="Beta. Are parts of the html matching with known cookie code?"
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    cookies: MetadataTags = Field(
        default=None,
        description="Alpha. Are cookies set and are they not whitelisted? "
        "Currently, there is no whitelist, yet."
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    fanboy_annoyance: MetadataTags = Field(
        default=None,
        description="Beta. Code that indicates 'annoying' behaviour."
        "Probability = "
        "Ratio of matching elements.",
    )
    fanboy_notification: MetadataTags = Field(
        default=None,
        description="Beta. Code that indicates notifications."
        "Probability = "
        "Ratio of matching elements.",
    )
    fanboy_social_media: MetadataTags = Field(
        default=None,
        description="Beta. Code that indicates social media links and content."
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    anti_adblock: MetadataTags = Field(
        default=None,
        description="Beta. Code that indicates anti adblock walls."
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    easylist_germany: MetadataTags = Field(
        default=None,
        description="Beta. A blocking list specific for Germany."
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    easylist_adult: MetadataTags = Field(
        default=None,
        description="Beta. A blocking list specific adult/PG18 content."
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    paywall: MetadataTags = Field(
        default=None,
        description="Alpha. Keywords indicating paywalls."
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    content_security_policy: MetadataTags = Field(
        default=None,
        description="Release. Are security policies set?"
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    iframe_embeddable: MetadataTags = Field(
        default=None,
        description="Release. Are iFrames embeddable?"
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    pop_up: MetadataTags = Field(
        default=None,
        description="Alpha. Are pop ups present?"
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    reg_wall: MetadataTags = Field(
        default=None,
        description="Alpha. Are registration walls present?"
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    log_in_out: MetadataTags = Field(
        default=None,
        description="Alpha. Is content present that indicates log in or out forms?"
        "Probability = "
        "1 If any matching element is found, else 0.",
    )
    accessibility: MetadataTags = Field(
        default=None,
        description="Beta. Google Lighthouse based calculation of accessibility"
        "Probability = "
        "1 if the website is 100% accessible, "
        "0 if the website is not accessible at all.",
    )
    g_d_p_r: MetadataTags = Field(
        default=None,
        description="Alpha. Are there indications that GDPR is obeyed?"
        "Probability = "
        "The more indicators are found the higher this value is.",
    )
    javascript: MetadataTags = Field(
        default=None,
        description="Alpha. Is there javascript among the files of this website?"
        "Probability = "
        "Ratio fo javascript files versus all files.",
    )


class Input(BaseModel):
    url: str = Field(..., description="The base url of the scraped website.")
    html: Optional[str] = Field(
        default="", description="Everything scraped from the website as text."
    )
    headers: Optional[str] = Field(
        default="", description="The response header interpretable as dict."
    )
    har: Optional[str] = Field(
        default="", description="The har object interpretable as json."
    )
    allow_list: Optional[ListTags] = Field(
        default=ListTags(),
        description="A list of key:bool pairs. "
        "Any metadata key == True will be extracted. "
        "If this list is not given, all values will be extracted.",
    )
    debug: Optional[bool] = Field(
        default=True,
        description="Developer flag to receive more information through API",
    )


class Output(BaseModel):
    url: str = Field(..., description="The base url of the scraped website.")
    meta: ExtractorTags = Field(
        default=None,
        description="The extracted metadata.",
    )
    exception: str = Field(
        default=None,
        description="A description of the exception which caused the extraction to fail.",
    )
    time_until_complete: float = Field(
        default=-1,
        description="The time needed from starting the extraction"
        " until sending the resulting meta data out.",
    )


app = FastAPI(title="Metadata Extractor", version="0.1")
app.communicator: QueueCommunicator


def _convert_dict_to_output_model(meta, debug: bool = False) -> ExtractorTags:
    out = ExtractorTags()
    for key in ExtractorTags.__fields__.keys():
        if key in meta.keys() and VALUES in meta[key]:

            if not debug or TIME_REQUIRED not in meta[key].keys():
                meta[key][TIME_REQUIRED] = None
            out.__setattr__(
                key,
                MetadataTags(
                    values=meta[key][VALUES],
                    probability=meta[key][PROBABILITY],
                    decision=meta[key][DECISION],
                    time_for_completion=meta[key][TIME_REQUIRED],
                ),
            )

    return out


def _convert_allow_list_to_dict(allow_list: ListTags) -> dict:
    return json.loads(allow_list.json())


@app.post("/extract_meta", response_model=Output)
def extract_meta(input_data: Input):
    starting_extraction = get_utc_now()

    allowance = _convert_allow_list_to_dict(input_data.allow_list)

    uuid = app.communicator.send_message(
        {
            MESSAGE_URL: input_data.url,
            MESSAGE_HTML: input_data.html,
            MESSAGE_HEADERS: input_data.headers,
            MESSAGE_HAR: input_data.har,
            MESSAGE_ALLOW_LIST: allowance,
        }
    )

    meta_data: dict = app.communicator.get_message(uuid)

    if meta_data:
        extractor_tags = _convert_dict_to_output_model(
            meta_data, input_data.debug
        )

        if MESSAGE_EXCEPTION in meta_data.keys():
            exception = meta_data[MESSAGE_EXCEPTION]
        else:
            exception = None

    else:
        extractor_tags = None
        exception = "No response from metadata extractor."

    out = Output(
        url=input_data.url,
        meta=extractor_tags,
        exception=exception,
        time_until_complete=get_utc_now() - starting_extraction,
    )

    return out


@app.get("/_ping")
def ping():
    return {"status": "ok"}
