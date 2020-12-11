import json
import subprocess

import uvicorn as uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

from lib.constants import ACCESSIBILITY, DESKTOP, SCORE

app = FastAPI(title="Lighthouse Extractor", version="0.1")

API_PORT = 5058


class Output(BaseModel):
    score: float = Field(
        default=-1,
        description="The accessibility score.",
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


@app.get("/accessibility", response_model=Output)
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

    std_out = []

    for line in iter(p.stdout.readline, b""):
        std_out.append(line.decode())
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


uvicorn.run(app, host="0.0.0.0", port=API_PORT, log_level="info")
