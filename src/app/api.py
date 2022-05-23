import json
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.communication import Message
from app.models import (
    DeleteCacheInput,
    DeleteCacheOutput,
    ExtractorTags,
    Input,
    MetadataTags,
    Output,
    Ping,
)
from app.schemas import CacheOutput
from cache.cache_manager import CacheManager
from core.metadata_manager import MetadataManager
from db.db import load_cache
from lib.constants import (
    EXPLANATION,
    MESSAGE_EXCEPTION,
    MESSAGE_URL,
    METADATA_EXTRACTOR,
    STAR_CASE,
    TIME_REQUIRED,
    VALUES,
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


def _convert_dict_to_output_model(meta: dict, debug: bool = False) -> ExtractorTags:
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


@app.post(
    "/extract_meta",
    response_model=Output,
    description="The main endpoint for metadata extraction.",
)
async def extract_meta(input_data: Input):
    starting_extraction = get_utc_now()

    allowance = json.loads(input_data.allow_list.json())

    # build a list of extractors that are set to True
    whitelist = None if input_data.allow_list is None else [k for k, v in allowance.items() if v]
    bypass_cache = False if input_data.bypass_cache is None else input_data.bypass_cache
    meta_data: dict = await app.manager.start(
        message=Message(
            url=input_data.url,
            splash_response=input_data.splash_response,
            whitelist=whitelist,
            bypass_cache=bypass_cache,
        )
    )

    if meta_data:
        extractor_tags = _convert_dict_to_output_model(meta_data, input_data.debug)

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
        exception=exception,
        time_until_complete=end_time - starting_extraction,
    )

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


# Developer endpoints
if not is_production_environment():

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
        cache_manager = CacheManager()
        row_count = cache_manager.reset_cache(reset_input.domain)
        return {"deleted_rows": row_count}
