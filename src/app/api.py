import multiprocessing
import queue
from typing import Optional
from uuid import uuid4, UUID

from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import Response


# TODO Taken from firmware, refactor!
class ProcessToDaemonCommunication:

    def __init__(self, send_queue: multiprocessing.Queue, receive_queue: multiprocessing.Queue):
        self._send_queue = send_queue
        self._receive_queue = receive_queue
        self._request_queue = {}

    def send_message(self, message: dict):
        uuid = uuid4()
        try:
            self._send_queue.put({uuid: message}, block=True, timeout=1)
            return uuid
        except queue.Full:
            return None

    def _receive_message(self) -> bool:
        try:
            response = self._receive_queue.get(block=True, timeout=1)
            if type(response) == dict:
                for uuid, message in response.items():
                    self._request_queue.update({uuid: message})
                    return True
        except queue.Empty:
            print("Queue empty")
            return False

    def get_message(self, uuid: UUID) -> Optional[dict]:
        tries = 1  # TODO: possible growing dict with each failed attempt
        self._receive_message()
        while uuid not in self._request_queue.keys() and tries <= 25:
            print(f"waited {tries} times for {uuid}")
            self._receive_message()
            tries += 1

        if uuid in self._request_queue.keys():
            message = self._request_queue[uuid]
            del self._request_queue[uuid]

            return message
        else:
            print("No return message received")
            return None


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
def extract_meta(response: Response, input_data: Input):
    uuid = app.api_queue.send_message({"url": input_data.url, "content": input_data.content})

    result: dict = app.api_queue.get_message(uuid)

    out = Output(url=input_data.url, meta={"content_lenght": len(result), "result": result})
    return out
