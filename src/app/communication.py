import multiprocessing
import queue
from typing import Optional
from uuid import UUID, uuid4

from lib.settings import API_RETRIES


class QueueCommunicator:
    def __init__(
        self,
        send_queue: multiprocessing.Queue,
        receive_queue: multiprocessing.Queue,
    ):
        self._send_queue = send_queue
        self._receive_queue = receive_queue
        self._request_queue = {}

    def send_message(self, message: dict) -> Optional[UUID]:
        try:
            uuid = uuid4()
            self._send_queue.put({uuid: message}, block=True, timeout=1)
        except queue.Full:
            uuid = None
        return uuid

    def _receive_message(self) -> None:
        try:
            response = self._receive_queue.get(block=True, timeout=1)
            if isinstance(response, dict):
                for uuid, message in response.items():
                    self._request_queue.update({uuid: message})
        except queue.Empty:
            print("Queue empty")

    def get_message(self, uuid: UUID) -> Optional[dict]:
        tries = 1
        self._receive_message()
        while uuid not in self._request_queue.keys() and tries <= API_RETRIES:
            print(f"waited {tries} times for {uuid}")
            self._receive_message()
            tries += 1

        if uuid in self._request_queue.keys():
            message = self._request_queue[uuid]
            del self._request_queue[uuid]
        else:
            message = None
            print("No return message received")

        return message
