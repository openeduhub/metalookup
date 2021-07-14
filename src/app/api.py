import json
from multiprocessing import shared_memory

from fastapi import FastAPI

from app.communication import QueueCommunicator
from app.models import (
    Explanation,
    ExtractorTags,
    Input,
    ListTags,
    MetadataTags,
    Output,
)
from lib.constants import (
    DECISION,
    MESSAGE_ALLOW_LIST,
    MESSAGE_EXCEPTION,
    MESSAGE_HAR,
    MESSAGE_HEADERS,
    MESSAGE_HTML,
    MESSAGE_SHARED_MEMORY_NAME,
    MESSAGE_URL,
    METADATA_EXTRACTOR,
    PROBABILITY,
    TIME_REQUIRED,
    VALUES,
)
from lib.settings import NUMBER_OF_EXTRACTORS, VERSION
from lib.timing import get_utc_now

app = FastAPI(title=METADATA_EXTRACTOR, version=VERSION)
app.communicator: QueueCommunicator
shared_status = shared_memory.ShareableList([0])


def _convert_dict_to_output_model(
    meta: dict, debug: bool = False
) -> ExtractorTags:
    extractor_tags = ExtractorTags()
    for key in ExtractorTags.__fields__.keys():
        if key in meta.keys() and VALUES in meta[key]:

            if not debug or TIME_REQUIRED not in meta[key].keys():
                meta[key][TIME_REQUIRED] = None

            extractor_tags.__setattr__(
                key,
                MetadataTags(
                    values=meta[key][VALUES],
                    probability=meta[key][PROBABILITY],
                    decision=meta[key][DECISION],
                    time_for_completion=meta[key][TIME_REQUIRED],
                    explanation=[Explanation.none, Explanation.NoHTTPS],
                ),
            )

    return extractor_tags


def _convert_allow_list_to_dict(allow_list: ListTags) -> dict:
    return json.loads(allow_list.json())


@app.post(
    "/extract_meta",
    response_model=Output,
    description="The main endpoint for metadata extraction.",
)
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
            MESSAGE_SHARED_MEMORY_NAME: shared_status.shm.name,
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
        exception = f"No response from {METADATA_EXTRACTOR}."

    out = Output(
        url=input_data.url,
        meta=extractor_tags,
        exception=exception,
        time_until_complete=get_utc_now() - starting_extraction,
    )

    return out


@app.get("/_ping", description="Ping function for automatic health check.")
def ping():
    return {"status": "ok"}


@app.get(
    "/get_progress",
    description="Returns progress of the metadata extraction. From 0 to 1 (=100%).",
)
def get_progress():
    return {
        "progress": round(shared_status[0] / NUMBER_OF_EXTRACTORS, 2),
    }
