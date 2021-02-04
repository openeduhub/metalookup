import json
import subprocess

import uvicorn as uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

from lib.constants import ACCESSIBILITY, DESKTOP, LIGHTHOUSE_EXTRACTOR, SCORE
from lib.settings import LIGHTHOUSE_API_PORT, VERSION

app = FastAPI(title=LIGHTHOUSE_EXTRACTOR, version=str(VERSION))


class Output(BaseModel):
    score: float = Field(
        default=-1,
        description=f"The {ACCESSIBILITY} score.",
    )


class Input(BaseModel):
    url: str = Field(..., description="The base url of the scraped website.")
    strategy: str = Field(
        default=DESKTOP,
        description="Whether to use mobile or desktop.",
    )
    category: str = Field(
        default=ACCESSIBILITY,
        description="Which category to evaluate. Only one for now",
    )


@app.get(f"/{ACCESSIBILITY}", response_model=Output)
def accessibility(input_data: Input):
    url = input_data.url
    strategy = input_data.strategy
    category = input_data.category
    cmd = [
        "lighthouse",
        url,
        "--enable-error-reporting",
        "--chrome-flags='--headless --no-sandbox --disable-gpu'",
        f"--emulated-form-factor={strategy}",
        f"--only-categories={category}",
        "--output=json",
        "--quiet",
    ]

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    std_out = [line.decode() for line in iter(p.stdout.readline, b"")]

    std_out = json.loads("".join(std_out))

    output = Output()
    try:
        if "runtimeError" in std_out.keys():
            output.score = [-1]
        else:
            output.score = std_out["categories"][category][SCORE]
    except KeyError:
        output.score = [-1]

    return output


@app.get("/_ping")
def ping():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        app, host="0.0.0.0", port=LIGHTHOUSE_API_PORT, log_level="info"
    )
