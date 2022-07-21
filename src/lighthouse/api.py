import asyncio
import json
import logging
import os
import subprocess
from time import perf_counter
from typing import List

import pydantic
import uvicorn as uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, HttpUrl, constr

# the timeout that lighthouse internally uses when loading the website
LOAD_TIMEOUT = int(os.environ.get("LOAD_TIMEOUT", 120))
logger = logging.getLogger("lighthouse")
app = FastAPI(title="Lighthouse Accessibility Extractor", version="1.0")


class Output(BaseModel):
    score: List[float] = Field(
        default=[-1.0],
        description="The accessibility score.",
    )


class Input(BaseModel):
    url: HttpUrl = Field(..., description="The base url of the scraped website.")
    strategy: constr(regex="(desktop|mobile)") = Field(  # noqa
        default="desktop", description="Defines for which target platform the accessibility will be calculated."
    )
    category: constr(regex="(accessibility)") = Field(
        default="accessibility",
        description="Which category to evaluate. Only one for now",
    )


@app.post("/accessibility", response_model=Output)
async def accessibility(input_data: Input):
    # NOTE: Make sure all string interpolations and inputs into the args are sanitized.
    #       Not doing so potentially provides a remote code execution exploit as the arguments
    #       are passed to process.Popen.
    args = [
        input_data.url,  # sanitized via HttUrl annotation in input base model
        "--enable-error-reporting",
        # See https://github.com/GoogleChrome/lighthouse/issues/6512 for discussion about timeouts
        "--chrome-flags='--headless --no-sandbox --disable-gpu --disable-dev-shm-usage'",
        f"--formFactor={input_data.strategy}",  # sanitized via regex in input based model
        f"--max-wait-for-load={LOAD_TIMEOUT * 1000}",
        f"--only-categories={input_data.category}",  # sanitized via regex in input based model
        "--output=json",
        "--quiet",
        f"{'--screenEmulation.mobile=true' if input_data.strategy == 'mobile' else '--no-screenEmulation.mobile'}",
    ]
    logger.debug(f"launching subprocess for {input_data}")

    # cant use metalookup.lib.tools.runtime, as the metalookup package is not available in this environment
    start = perf_counter()
    process = await asyncio.create_subprocess_exec("lighthouse", *args, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    logger.debug(f"awaiting outputs for {input_data}")
    stdout, stderr = await process.communicate()
    runtime = perf_counter() - start
    logger.info(f"Subprocess call for {input_data.url} took {runtime:3.2f}s")

    if process.returncode != 0:
        raise HTTPException(
            status_code=502,
            detail=f"Lighthouse process exited with code {process.returncode}. Standard Error: {stderr.decode()}",
        )

    try:
        logger.debug(f"building response for {input_data}")
        output = json.loads(stdout.decode())
        return Output(score=[output["categories"][input_data.category]["score"]])
    except pydantic.error_wrappers.ValidationError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not interpret lighthouse output: {e}. Raw output:\n{stdout.decode()}",
        )
    except json.decoder.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to deserialize lighthouse standard output: {e}. Standard Output: {stdout.decode()}",
        )


@app.get("/_ping")
async def ping():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5058, log_level="info")
