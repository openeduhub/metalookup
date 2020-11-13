import multiprocessing
import signal
import time
from queue import Empty

import uvicorn

from app.api import app
from app.communication import ProcessToDaemonCommunication
from features.metadata_manager import MetadataManager
from lib.constants import MESSAGE_EXCEPTION, MESSAGE_HTML, MESSAGE_META
from lib.logger import create_logger
from lib.settings import API_PORT
from lib.timing import get_utc_now


class Manager:
    run_loop: bool = False

    def __init__(self):

        self._logger = create_logger()

        self._create_api()

        self.metadata_manager = MetadataManager.get_instance()
        self.metadata_manager.setup()

        self.run_loop = True

        self.run()

    def _create_api(self):
        self.api_to_manager_queue = multiprocessing.Queue()
        self.manager_to_api_queue = multiprocessing.Queue()
        api_process = multiprocessing.Process(
            target=api_server,
            args=(self.api_to_manager_queue, self.manager_to_api_queue),
        )
        api_process.start()

    # =========== LOOP ============
    def handle_content(self, request):

        self._logger.debug(f"request: {request}")
        for uuid, message in request.items():
            self._logger.debug(f"message: {message}")

            if message[MESSAGE_HTML] == "":
                response = {
                    MESSAGE_META: {},
                    MESSAGE_EXCEPTION: "No html data given and no stand-alone scraper built in yet.",
                }
            else:
                response = self.metadata_manager.start(message=message)

            self.manager_to_api_queue.put({uuid: response})

    def get_api_request(self):
        if self.api_to_manager_queue is not None:
            try:
                request = self.api_to_manager_queue.get(
                    block=False, timeout=0.1
                )
                if isinstance(request, dict):
                    self.handle_content(request)
            except Empty:
                pass

    def run(self):
        signal.signal(signal.SIGINT, self._graceful_shutdown)
        signal.signal(signal.SIGTERM, self._graceful_shutdown)

        while self.run_loop:
            self.get_api_request()
            self._logger.info(f"Current time: {get_utc_now()}")
            time.sleep(1)

    def _graceful_shutdown(self, signum=None, frame=None):
        self.run_loop = False


def api_server(queue, return_queue):
    app.api_queue = ProcessToDaemonCommunication(queue, return_queue)
    uvicorn.run(app, host="0.0.0.0", port=API_PORT, log_level="info")


if __name__ == "__main__":
    manager = Manager()
