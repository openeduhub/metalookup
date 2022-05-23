from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models import DeleteCacheInput, DeleteCacheOutput, Input, Output, Ping
from app.schemas import CacheOutput
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


@app.on_event("startup")
async def initialize_manager():
    app.logger = create_logger()
    app.logger.info("Startup")
    app.manager = await MetadataManager.create()


@app.post(
    "/extract_meta",
    response_model=Output,
    description="The main endpoint for metadata extraction.",
)
async def extract_meta(input: Input):
    app.logger.info(f"Received request for {input.url}")

    return await app.manager.extract(input)


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
