import logging

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

import lib.settings
from app.models import DeleteCacheInput, DeleteCacheOutput, Input, MetadataTags, Output, Ping
from caching.backends import DatabaseBackend
from caching.cache import cache
from core.metadata_manager import MetadataManager
from lib.logger import setup_logging
from lib.tools import runtime

setup_logging(level=lib.settings.LOG_LEVEL, path=lib.settings.LOG_PATH)

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
cache_backend = DatabaseBackend(url=lib.settings.CACHE_DATABASE_URL) if lib.settings.ENABLE_CACHE else None


@app.on_event("startup")
async def initialize():
    await manager.setup()
    if cache_backend is not None:
        await cache_backend.setup()


@app.middleware("http")
async def caching_and_response_time(request: Request, call_next):
    with runtime() as t:
        response = await call_next(request)
    response.headers["X-Process-Time"] = f"{t():5.2f}"
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
if lib.settings.ENABLE_CACHE_CONTROL_ENDPOINTS:

    @app.get(
        "/cache",
        response_model=list[Output],
        description="Developer endpoint to receive cache content.",
    )
    def get_cache():
        return []  # fixme

    @app.delete(
        "/cache",
        description="Endpoint to delete the cache",
        response_model=DeleteCacheOutput,
    )
    def delete_cache(reset_input: DeleteCacheInput):
        return DeleteCacheOutput()  # fixme:
