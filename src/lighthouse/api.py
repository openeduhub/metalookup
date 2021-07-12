import json
import subprocess
from typing import List

import uvicorn as uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

from lib.constants import (
    ACCESSIBILITY,
    DESKTOP,
    LIGHTHOUSE_EXTRACTOR,
    MOBILE,
    SCORE,
)
from lib.settings import LIGHTHOUSE_API_PORT, VERSION

app = FastAPI(title=LIGHTHOUSE_EXTRACTOR, version=str(VERSION))


class Output(BaseModel):
    score: List[float] = Field(
        default=[-1.0],
        description=f"The {ACCESSIBILITY} score.",
    )


class Input(BaseModel):
    url: str = Field(..., description="The base url of the scraped website.")
    strategy: str = Field(
        default=DESKTOP,
        description=f"Whether to use {MOBILE} or {DESKTOP}.",
    )
    category: str = Field(
        default=ACCESSIBILITY,
        description="Which category to evaluate. Only one for now",
    )


@app.get(f"/{ACCESSIBILITY}", response_model=Output)
def accessibility(input_data: Input):
    lighthouse_command = [
        "lighthouse",
        input_data.url,
        "--enable-error-reporting",
        "--chrome-flags='--headless --no-sandbox --disable-gpu'",
        f"--emulated-form-factor={input_data.strategy}",
        f"--only-categories={input_data.category}",
        "--output=json",
        "--quiet",
    ]

    lighthouse_process = subprocess.Popen(
        lighthouse_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    lighthouse_output = "".join(
        [
            line.decode()
            for line in iter(lighthouse_process.stdout.readline, b"")
        ]
    )
    try:
        lighthouse_output = json.loads(lighthouse_output)
    except json.decoder.JSONDecodeError as e:
        lighthouse_output = {"runtimeError": None}

    output = Output()
    output.score = [-1.0]
    try:
        if "runtimeError" not in lighthouse_output.keys():
            output.score = lighthouse_output["categories"][
                input_data.category
            ][SCORE]
    except KeyError:
        pass

    return output


@app.get("/_ping")
def ping():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        app, host="0.0.0.0", port=LIGHTHOUSE_API_PORT, log_level="info"
    )
