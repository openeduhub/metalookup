import json
from multiprocessing import shared_memory

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

import db.base
from app import db_models
from app.communication import QueueCommunicator
from app.db_models import RecordSchema
from app.models import (
    DecisionCase,
    Explanation,
    ExtractorTags,
    Input,
    ListTags,
    MetadataTags,
    Output,
)
from db.db import (
    create_dummy_record,
    create_request_record,
    create_response_record,
    get_db,
)
from lib.constants import (
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
# noinspection PyTypeHints
app.communicator: QueueCommunicator

shared_status = shared_memory.ShareableList([0])
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
                    probability=meta[key][PROBABILITY],
                    isHappyCase=DecisionCase.UNKNOWN,  # TODO: resolve properly, formerly meta[key][DECISION],
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

    database_exception = ""
    try:
        create_request_record(
            starting_extraction, input_data=input_data, allowance=allowance
        )
    except OperationalError as err:
        database_exception += "\nDatabase exception: " + str(err.args)

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
            exception = ""

    else:
        extractor_tags = None
        exception = f"No response from {METADATA_EXTRACTOR}."

    end_time = get_utc_now()
    if exception != "":
        raise HTTPException(
            status_code=400,
            detail={
                MESSAGE_EXCEPTION: exception,
                "time_until_complete": end_time - starting_extraction,
                MESSAGE_URL: input_data.url,
            },
        )

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
        database_exception += "\nDatabase exception: " + str(err.args)
        out.exception += database_exception

    return out


@app.get("/records/")
def show_records(database: Session = Depends(get_db)):
    try:
        records = database.query(db_models.Record).all()
    except OperationalError as err:
        dummy_record = create_dummy_record()
        dummy_record.exception = f"Database exception: {err.args}"
        records = [dummy_record]

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
    return {"out": records}


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
