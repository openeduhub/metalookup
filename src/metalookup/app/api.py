import logging
import multiprocessing
from multiprocessing import Process
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import HttpUrl

import metalookup.lib.settings
from metalookup.app.models import Input, MetadataTags, Output, Ping
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
    key=lambda input, request, response, extra: f"{input.url}-{extra}" if input.splash_response is None else None,
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
