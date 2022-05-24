import time

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.models import DeleteCacheInput, DeleteCacheOutput, Input, MetadataTags, Output, Ping
from app.schemas import CacheOutput
from caching.backends import InMemoryBackend
from caching.cache import cache
from core.metadata_manager import MetadataManager
from lib.logger import create_logger
from lib.tools import is_production_environment

app = FastAPI(title="meta-lookup", version="v1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["*"],
)
app.cache_backend = InMemoryBackend()


@app.on_event("startup")
async def initialize():
    app.logger = create_logger()
    app.logger.info("Startup")
    app.manager = await MetadataManager.create()
    # await app.cache_backend.setup()


@app.middleware("http")
async def caching_and_response_time(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2) / 1000)
    return response


@app.post(
    "/extract_meta",
    response_model=Output,
    description="The main endpoint for metadata extraction.",
)
@cache(
    expire=24 * 60 * 60 * 28,
    key=lambda input, request, response: str(input.url) if input.splash_response is None else None,
    backend=app.cache_backend,
)
# request and response arguments are needed for the cache wrapper.
async def extract_meta(input: Input, request: Request, response: Response):
    """The extract endpoint"""
    app.logger.info(f"Received request for {input.url}")

    result = await app.manager.extract(input)

    # prevent caching of responses that do not contain a full set of metadata information.
    if any(not isinstance(getattr(result, extractor.key), MetadataTags) for extractor in app.manager.extractors):
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
if not is_production_environment():

    @app.get(
        "/cache",
        response_model=CacheOutput,
        description="Developer endpoint to receive cache content.",
    )
    def get_cache():
        return CacheOutput()  # fixme

    @app.delete(
        "/cache",
        description="Endpoint to delete the cache",
        response_model=DeleteCacheOutput,
    )
    def delete_cache(reset_input: DeleteCacheInput):
        return DeleteCacheOutput()  # fixme:
