from fastapi import FastAPI
from pydantic import BaseModel

from app.communication import ProcessToDaemonCommunication
from lib.config import MESSAGE_CONTENT, MESSAGE_URL
from lib.timing import get_utc_now


class Input(BaseModel):
    url: str
    content: dict


class Output(BaseModel):
    url: str
    meta: dict


app = FastAPI()
app.api_queue: ProcessToDaemonCommunication


@app.post("/extract_meta", response_model=Output)
def extract_meta(input_data: Input):
    starting_extraction = get_utc_now()
    uuid = app.api_queue.send_message(
        {MESSAGE_URL: input_data.url, MESSAGE_CONTENT: input_data.content}
    )

    meta_data: dict = app.api_queue.get_message(uuid)

    meta_data.update(
        {"time_until_complete": get_utc_now() - starting_extraction}
    )
    out = Output(url=input_data.url, meta=meta_data)
    return out


@app.get("/_ping")
def ping():
    return {"status": "ok"}
