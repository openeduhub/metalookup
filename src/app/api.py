import json
import traceback
from multiprocessing import shared_memory

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

import db.base
from app.communication import QueueCommunicator
from app.models import (
    DeleteCacheInput,
    DeleteCacheOutput,
    ExtractorTags,
    Input,
    ListTags,
    MetadataTags,
    Output,
    Ping,
    ProgressInput,
    ProgressOutput,
)
from app.schemas import CacheOutput, RecordSchema, RecordsOutput
from cache.cache_manager import CacheManager
from db.db import (
    create_request_record,
    create_response_record,
    load_cache,
    load_records,
)
from lib.constants import (
    EXPLANATION,
    STAR_CASE,
    MESSAGE_ALLOW_LIST,
    MESSAGE_BYPASS_CACHE,
    MESSAGE_EXCEPTION,
    MESSAGE_HAR,
    MESSAGE_HEADERS,
    MESSAGE_HTML,
    MESSAGE_SHARED_MEMORY_NAME,
    MESSAGE_URL,
    METADATA_EXTRACTOR,
    TIME_REQUIRED, VALUES,
)
from lib.settings import NUMBER_OF_EXTRACTORS, VERSION
from lib.timing import get_utc_now
from lib.tools import is_production_environment

app = FastAPI(title=METADATA_EXTRACTOR, version=VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["*"],
)
# noinspection PyTypeHints
app.communicator: QueueCommunicator

shared_status = shared_memory.ShareableList([0, " " * 1024])
db.base.create_metadata(db.base.database_engine)


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
                    stars=meta[key][STAR_CASE],
                    time_for_completion=meta[key][TIME_REQUIRED],
                    explanation=meta[key][EXPLANATION],
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

    database_exception = ""
    try:
        create_request_record(
            starting_extraction, input_data=input_data, allowance=allowance
        )
    except OperationalError as err:
        database_exception += (
            "\nDatabase exception: "
            + str(err.args)
            + "".join(traceback.format_exception(None, err, err.__traceback__))
        )

    uuid = app.communicator.send_message(
        {
            MESSAGE_URL: input_data.url,
            MESSAGE_HTML: input_data.html,
            MESSAGE_HEADERS: input_data.headers,
            MESSAGE_HAR: input_data.har,
            MESSAGE_ALLOW_LIST: allowance,
            MESSAGE_SHARED_MEMORY_NAME: shared_status.shm.name,
            MESSAGE_BYPASS_CACHE: input_data.bypass_cache,
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
            exception = ""

    else:
        extractor_tags = None
        exception = f"No response from {METADATA_EXTRACTOR}."

    end_time = get_utc_now()
    out = Output(
        url=input_data.url,
        meta=extractor_tags,
        exception=exception + database_exception,
        time_until_complete=end_time - starting_extraction,
    )
    try:
        create_response_record(
            starting_extraction,
            end_time,
            input_data=input_data,
            allowance=allowance,
            output=out,
        )
    except OperationalError as err:
        database_exception += (
            "\nDatabase exception: "
            + str(err.args)
            + "".join(traceback.format_exception(None, err, err.__traceback__))
        )
        out.exception += database_exception

    if exception != "":
        raise HTTPException(
            status_code=400,
            detail={
                MESSAGE_URL: input_data.url,
                "meta": meta_data,
                MESSAGE_EXCEPTION: exception,
                "time_until_complete": end_time - starting_extraction,
            },
        )

    return out


@app.get(
    "/_ping",
    description="Ping function for automatic health check.",
    response_model=Ping,
)
def ping():
    # TODO: Have this check manager health, too
    return {"status": "ok"}


@app.get(
    "/get_progress",
    description="Returns progress of the metadata extraction. From 0 to 1 (=100%).",
    response_model=ProgressOutput,
)
def get_progress(progress_input: ProgressInput):
    if (
        progress_input.url != ""
        and shared_status[1] != ""
        and shared_status[1] in progress_input.url
    ):
        progress = round(shared_status[0] / NUMBER_OF_EXTRACTORS, 2)
    else:
        progress = -1
    return {
        "progress": progress,
    }


# Developer endpoints
if not is_production_environment():

    @app.get(
        "/records",
        response_model=RecordsOutput,
        description="Get all urls and their processed metadata.",
    )
    def show_records():
        records = load_records()
        out = []
        for record in records:
            out.append(
                RecordSchema(
                    id=record.id,
                    timestamp=record.timestamp,
                    start_time=record.start_time,
                    action=record.action,
                    allow_list=record.allow_list,
                    meta=record.meta,
                    url=record.url,
                    html=record.html,
                    headers=record.headers,
                    har=record.har,
                    debug=record.debug,
                    exception=record.exception,
                    time_until_complete=record.time_until_complete,
                )
            )
        return {"records": out}

    @app.get(
        "/cache",
        response_model=CacheOutput,
        description="Developer endpoint to receive cache content.",
    )
    def get_cache():
        return {"cache": load_cache()}

    @app.delete(
        "/cache",
        description="Endpoint to delete the cache",
        response_model=DeleteCacheOutput,
    )
    def delete_cache(reset_input: DeleteCacheInput):
        cache_manager = CacheManager.get_instance()
        row_count = cache_manager.reset_cache(reset_input.domain)
        return {"deleted_rows": row_count}
