import multiprocessing
import queue
from typing import Optional
from uuid import UUID, uuid4

from lib.settings import API_RETRIES


class ProcessToDaemonCommunication:
    def __init__(
        self,
        send_queue: multiprocessing.Queue,
        receive_queue: multiprocessing.Queue,
    ):
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
            if isinstance(response, dict):
                for uuid, message in response.items():
                    self._request_queue.update({uuid: message})
                    return True
        except queue.Empty:
            print("Queue empty")
        return False

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

            return message

        print("No return message received")
        return None
