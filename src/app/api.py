import json
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.communication import ProcessToDaemonCommunication
from lib.constants import (
    DECISION,
    MESSAGE_ALLOW_LIST,
    MESSAGE_EXCEPTION,
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
    advertisement: Optional[bool] = True
    easy_privacy: Optional[bool] = True
    malicious_extensions: Optional[bool] = True
    extracted_links: Optional[bool] = True
    extract_from_files: Optional[bool] = True
    internet_explorer_tracker: Optional[bool] = True
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


class ExtractorTags(BaseModel):
    advertisement: MetadataTags = Field(default=None)
    easy_privacy: MetadataTags = Field(default=None)
    malicious_extensions: MetadataTags = Field(default=None)
    extract_from_files: MetadataTags = Field(default=None)
    internet_explorer_tracker: MetadataTags = Field(default=None)
    cookies: MetadataTags = Field(default=None)
    fanboy_annoyance: MetadataTags = Field(default=None)
    fanboy_notification: MetadataTags = Field(default=None)
    fanboy_social_media: MetadataTags = Field(default=None)
    anti_adblock: MetadataTags = Field(default=None)
    easylist_germany: MetadataTags = Field(default=None)
    easylist_adult: MetadataTags = Field(default=None)
    paywall: MetadataTags = Field(default=None)
    content_security_policy: MetadataTags = Field(default=None)
    iframe_embeddable: MetadataTags = Field(default=None)
    pop_up: MetadataTags = Field(default=None)
    reg_wall: MetadataTags = Field(default=None)
    log_in_out: MetadataTags = Field(default=None)
    accessibility: MetadataTags = Field(default=None)


class Input(BaseModel):
    url: str = Field(..., description="The base url of the scraped website.")
    html: Optional[str] = Field(
        default="", description="Everything scraped from the website as text."
    )
    headers: Optional[str] = Field(
        default="", description="The response header interpretable as dict."
    )
    allow_list: Optional[ListTags] = Field(
        default=ListTags(),
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
    time_until_complete: float = Field(
        default=-1,
        description="The time needed from starting the extraction"
        " until sending the resulting meta data out.",
    )


app = FastAPI(title="Metadata Extractor", version="0.1")
app.api_queue: ProcessToDaemonCommunication


def _convert_dict_to_output_model(meta) -> ExtractorTags:
    out = ExtractorTags()
    for key in ExtractorTags.__fields__.keys():
        if key in meta.keys() and VALUES in meta[key]:
            out.__setattr__(
                key,
                MetadataTags(
                    values=meta[key][VALUES],
                    probability=meta[key][PROBABILITY],
                    decision=meta[key][DECISION],
                ),
            )
    return out


def _convert_allow_list_to_dict(allow_list: ListTags) -> dict:
    return json.loads(allow_list.json())


@app.post("/extract_meta", response_model=Output)
def extract_meta(input_data: Input):
    starting_extraction = get_utc_now()

    allowance = _convert_allow_list_to_dict(input_data.allow_list)

    uuid = app.api_queue.send_message(
        {
            MESSAGE_URL: input_data.url,
            MESSAGE_HTML: input_data.html,
            MESSAGE_HEADERS: input_data.headers,
            MESSAGE_ALLOW_LIST: allowance,
        }
    )

    meta_data: dict = app.api_queue.get_message(uuid)

    if meta_data:
        extractor_tags = _convert_dict_to_output_model(meta_data)

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
