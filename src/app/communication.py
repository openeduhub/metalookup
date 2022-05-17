import multiprocessing
import queue
from dataclasses import dataclass
from typing import Any, Optional
from uuid import UUID, uuid4

from lib.settings import API_RETRIES


@dataclass(frozen=True)
class Message:
    """
    If a message is lacking any of the html, header, or har fields, then the URL will be
    used to issue a request and fetch the content, headers, and har. I.e the response will
    replace any potentially existing content, header, or har with the received response.
    """

    url: str
    """The url of the content to analyze."""
    html: Optional[str]
    """The content to analyze."""
    header: Optional[str]
    """The headers received together with the content."""
    har: Optional[dict[str, Any]]
    """Optional dictionary resembling the HTTP Archive format (https://en.wikipedia.org/wiki/HAR_(file_format))"""
    extractors: Optional[list[str]]
    """Which extractors (defined by their keys) to use. If none, then all extractors should be used."""
    bypass_cache: bool
    """Whether returning cached data is allowed."""
    _shared_memory_name: str  # fixme: unclear


class QueueCommunicator:
    def __init__(
        self,
        send_queue: multiprocessing.Queue,
        receive_queue: multiprocessing.Queue,
    ):
        self._send_queue = send_queue
        self._receive_queue = receive_queue
        self._request_queue = {}

    def send_message(self, message: Message) -> Optional[UUID]:
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
            print(f"Waited {tries} times messages from request queue.")
            self._receive_message()
            tries += 1

        if uuid in self._request_queue.keys():
            message = self._request_queue[uuid]
            del self._request_queue[uuid]
        else:
            message = None
            print("No return message received")

        return message
