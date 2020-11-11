from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.communication import ProcessToDaemonCommunication
from lib.constants import (
    DECISION,
    MESSAGE_HEADERS,
    MESSAGE_HTML,
    MESSAGE_URL,
    PROBABILITY,
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


class ListTags(BaseModel):
    advertisement: bool = False
    easy_privacy: bool = False
    extracted_links: bool = False
    extract_from_files: bool = False
    internet_explorer_tracker: bool = False
    cookies: bool = False
    fanboy_annoyance: bool = False
    fanboy_notification: bool = False
    fanboy_social_media: bool = False
    anti_adblock: bool = False
    easylist_germany: bool = False
    easylist_adult: bool = False
    paywall: bool = False
    content_security_policy: bool = False
    iframe_embeddable: bool = False
    pop_up: bool = False


class ExtractorTags(BaseModel):
    advertisement: Optional[MetadataTags]
    easy_privacy: Optional[MetadataTags]
    malicious_extensions: Optional[MetadataTags]
    extract_from_files: Optional[MetadataTags]
    internet_explorer_tracker: Optional[MetadataTags]
    cookies: Optional[MetadataTags]
    fanboy_annoyance: Optional[MetadataTags]
    fanboy_notification: Optional[MetadataTags]
    fanboy_social_media: Optional[MetadataTags]
    anti_adblock: Optional[MetadataTags]
    easylist_germany: Optional[MetadataTags]
    easylist_adult: Optional[MetadataTags]
    paywall: Optional[MetadataTags]
    content_security_policy: Optional[MetadataTags]
    iframe_embeddable: Optional[MetadataTags]
    pop_up: Optional[MetadataTags]


class Input(BaseModel):
    url: str = Field(..., description="The base url of the scraped website.")
    html: str = Field(
        ..., description="Everything scraped from the website as text."
    )
    headers: str = Field(
        ..., description="The response header interpretable as dict."
    )
    allow_list: Optional[ListTags] = Field(
        default=None,
        description="A list of key:bool pairs. "
        "Any metadata key == True will be extracted. "
        "If this list is not given, all values will be extracted.",
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


app = FastAPI(title="Metadata Extractor", version="0.1")
app.api_queue: ProcessToDaemonCommunication


def _convert_dict_to_output_model(meta):
    out = ExtractorTags()
    extractor_keys = ExtractorTags.__fields__.keys()
    for key in extractor_keys:
        if key in meta.keys() and VALUES in meta[key]:
            out.__setattr__(
                key,
                MetadataTags(
                    value=meta[key][VALUES],
                    probability=meta[key][PROBABILITY],
                    decision=meta[key][DECISION],
                ),
            )
    return out


@app.post("/extract_meta", response_model=Output)
def extract_meta(input_data: Input):
    starting_extraction = get_utc_now()
    uuid = app.api_queue.send_message(
        {
            MESSAGE_URL: input_data.url,
            MESSAGE_HTML: input_data.html,
            MESSAGE_HEADERS: input_data.headers,
        }
    )

    meta_data: dict = app.api_queue.get_message(uuid)

    if meta_data:
        meta_data.update(
            {"time_until_complete": get_utc_now() - starting_extraction}
        )
        _convert_dict_to_output_model(meta_data)

        out = Output(url=input_data.url, meta=meta_data)
    else:
        message = "No response from metadata extractor."
        out = Output(url=input_data.url, exception=message)

    return out


@app.get("/_ping")
def ping():
    return {"status": "ok"}
