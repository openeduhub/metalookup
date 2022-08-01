import logging
import multiprocessing
from multiprocessing import Process
from typing import Dict, Optional, Union

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import HttpUrl

import metalookup.lib.settings
from metalookup.app.models import Error, Input, LRMISuggestions, MetadataTags, Output, Ping, StarCase
from metalookup.caching.backends import DatabaseBackend
from metalookup.caching.cache import cache
from metalookup.caching.warmup import warmup
from metalookup.core.metadata_manager import MetadataManager
from metalookup.lib.logger import setup_logging
from metalookup.lib.tools import runtime

setup_logging(level=metalookup.lib.settings.LOG_LEVEL, path=metalookup.lib.settings.LOG_PATH)

logger = logging.getLogger(__name__)

app = FastAPI(title="meta-lookup", version="v1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["*"],
)

manager = MetadataManager()
cache_backend = (
    DatabaseBackend(url=metalookup.lib.settings.CACHE_DATABASE_URL) if metalookup.lib.settings.ENABLE_CACHE else None
)


@app.on_event("startup")
async def initialize():
    await manager.setup()
    if cache_backend is not None:
        await cache_backend.setup()


@app.middleware("http")
async def caching_and_response_time(request: Request, call_next):
    with runtime() as t:
        response = await call_next(request)
    response.headers["X-Process-Time"] = str(round(t(), 2))
    return response


@app.post(
    "/extract",
    response_model=Output,
    description="The main endpoint for metadata extraction.",
)
@cache(
    expire=24 * 60 * 60 * 28,
    key=lambda input, request, response, extra: f"{input.url}-{extra}",
    backend=cache_backend,
)
# request and response arguments are needed for the cache wrapper.
async def extract(input: Input, request: Request, response: Response, extra: bool = False):
    logger.info(f"Received request for {input.url}")

    result = await manager.extract(input, extra=extra)

    # prevent caching of responses that do not contain a full set of metadata information.
    if any(not isinstance(getattr(result, extractor.key), MetadataTags) for extractor in manager.extractors):
        response.headers.append("Cache-Control", "no-cache")
        response.headers.append("Cache-Control", "no-store")
    return result


@app.post(
    "/suggestions",
    response_model=LRMISuggestions,
    description="Use the available extractors to deduce PoC level suggestions for four of the meta data fields.",
)
@cache(
    expire=24 * 60 * 60 * 28,
    # Note, we simply modify the cache key here to use the same codebase as for the extract endpoint.
    key=lambda input, request, response: f"{input.url}-suggestions",
    backend=cache_backend,
)
# request and response arguments are needed for the cache wrapper.
async def suggest(input: Input, request: Request, response: Response):
    logger.info(f"Received request for {input.url}")

    result = await manager.extract(input, extra=True)

    def combine(*fields: str) -> Union[MetadataTags, Error]:
        """
        Combines the extractors' MetaDataTags for given extractors (the field names used in the Output model).
        Star rating will be deduced as minimum star rating.
        If any extractor failed, the combined result is also a failure listing all sub-failures.
        """
        fields: Dict[str, Union[Error, MetadataTags]] = {field: getattr(result, field) for field in fields}
        # check if any of the three extractors resulted in an error
        errors = {name: field.error for name, field in fields.items() if hasattr(field, "error")}
        if len(errors) > 0:
            return Error(error=f"Extractor errors: {errors}")
        return MetadataTags(
            stars=StarCase.from_number(min(int(field.stars) for field in fields.values())),
            explanation=(
                "Deduced from the minimum star rating of the following extractors.\n"
                + "\n".join(f"{name}-explanation: {field.explanation}" for name, field in fields.items())
            ),
            extra={name: field.extra for name, field in fields.items()},
        )

    return LRMISuggestions(
        protection_of_minors=combine("easylist_adult"),
        login=combine("log_in_out", "reg_wall", "paywall"),
        data_privacy=combine("easy_privacy", "gdpr", "cookies"),
        accessibility=combine("accessibility"),
    )


# todo (https://github.com/openeduhub/metalookup/issues/135): remove once frontend is transitioned to new API
@app.post(
    "/extract_meta",
    description="The legacy endpoint for metadata extraction.",
)
# request and response arguments are needed for the cache wrapper.
async def legacy_extract(input: Input, request: Request, response: Response):
    logger.info(f"Received legacy request for {input.url}")

    # need extra data for accessibility score below!
    result = await manager.extract(input, extra=True)

    logger.info(f"Translating to legacy response for {input.url} ")
    # if a required item is missing (e.g. because of an exception in the respective extractor, then we want
    # to have that information present in the frontend as diagnostic information for now
    try:
        return {
            # everything but the "meta" keyword is ignored in the current frontend implementation
            "meta": {
                # extractors in order as used in current frontend implementation html template
                "accessibility": {
                    # frontend uses values list to extract score :facepalm:
                    "values": [str(result.accessibility.extra.average_score)],
                    "stars": result.accessibility.stars.value,
                    "explanation": result.accessibility.explanation,
                },
                "advertisement": {
                    "stars": result.advertisement.stars.value,
                },
                "g_d_p_r": {
                    "stars": result.gdpr.stars.value,
                },
                "cookies": {
                    "stars": result.cookies.stars.value,
                },
                "fanboy_social_media": {
                    "stars": result.fanboy_social_media.stars.value,
                },
                "anti_adblock": {
                    "stars": result.anti_adblock.stars.value,
                },
                "easy_privacy": {
                    "stars": result.easy_privacy.stars.value,
                },
                "pop_up": {
                    "stars": result.pop_up.stars.value,
                },
                "paywall": {
                    "stars": result.paywall.stars.value,
                },
                "malicious_extensions": {
                    "stars": result.malicious_extensions.stars.value,
                },
                # not used in frontend
                # "extract_from_files": {},
                # "fanboy_annoyance": {},
                # "fanboy_notification": {},
                # "easylist_germany": {},
                # "easylist_adult": {},
                # "security": {},
                # "iframe_embeddable": {},
                # "reg_wall": {},
                # "log_in_out": {},
                # "javascript": {},
            },
        }
    except Exception as e:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=502,
            detail=f"Cannot build legacy data model from extracted information: {str(result)}.\n Reason: {e}",
        )


@app.get(
    "/_ping",
    description="Ping function for automatic health check.",
    response_model=Ping,
)
async def ping():
    # TODO: Have this check manager health, too
    return {"status": "ok"}


# Developer endpoints
if metalookup.lib.settings.ENABLE_CACHE_CONTROL_ENDPOINTS:
    # fixme: Not sure if this would work if the service is running with multiple uvicorn replications.
    """If there is a background task already running, then this variable should be not None"""
    process: Optional[Process] = None

    @app.post(
        "/cache/warmup",
        description="""
        Accepts a simple json list of urls for which the cache will be warmed up in the background.
        Once the background task is started, the request will return with a 202 (Accepted). While the background task
        is running, other requests to this endpoint will be answered with a 429 (Too many requests).
        """,
    )
    async def cache_warmup(urls: list[HttpUrl], response: Response):
        global process
        logger.info("Received cache-warmup request - dispatching background process")

        if process is None or not process.is_alive():
            # use spawn context to not pull in all the resources from the running service and instead start a "clean"
            # python interpreter: https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods
            ctx = multiprocessing.get_context("spawn")
            process = ctx.Process(target=warmup, args=(urls,), daemon=True)
            process.start()
            # we cannot join here (or in a background task) as that would block the request (or the entire service)
            response.status_code = 202  # "Accepted"
        else:
            response.status_code = 429  # "Too many requests"
