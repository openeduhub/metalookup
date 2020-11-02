from fastapi import FastAPI
from pydantic import BaseModel

from app.communication import ProcessToDaemonCommunication


class Input(BaseModel):
    url: str
    content: str
    result: dict


class Output(BaseModel):
    url: str
    meta: dict


app = FastAPI()
app.api_queue: ProcessToDaemonCommunication


@app.post('/extract_meta', response_model=Output)
def extract_meta(input_data: Input):
    uuid = app.api_queue.send_message({"url": input_data.url, "content": input_data.content})

    result: dict = app.api_queue.get_message(uuid)

    out = Output(url=input_data.url, meta={"content_lenght": len(result), "result": result})
    return out
