import cProfile
import multiprocessing
import signal
import sys
import time
import traceback
from queue import Empty

import uvicorn

from app.api import app
from app.communication import QueueCommunicator
from features.metadata_manager import MetadataManager
from lib.constants import MESSAGE_EXCEPTION
from lib.logger import create_logger
from lib.settings import API_PORT, WANT_PROFILING
from lib.timing import get_utc_now, global_start


class Manager:
    run_loop: bool = False
    api_process: multiprocessing.Process

    def __init__(self) -> None:

        self._logger = create_logger()

        self._create_api()

        self.metadata_manager = MetadataManager.get_instance()

        self.run_loop = True

        self._logger.info("Manager set up and waiting for data.")

        self.run()

    def _create_api(self) -> None:
        self.api_to_manager_queue = multiprocessing.Queue()
        self.manager_to_api_queue = multiprocessing.Queue()
        self.api_process = multiprocessing.Process(
            target=launch_api_server,
            args=(self.api_to_manager_queue, self.manager_to_api_queue),
        )
        self.api_process.start()

    # =========== LOOP ============
    def _handle_content(self, request: dict) -> None:

        self._logger.info(
            f"Received request: {request}, Number of items: {len(request.keys())}"
        )
        for uuid, message in request.items():
            self._logger.debug(f"message: {message}")

            try:
                response = self.metadata_manager.start(message=message)
            except Exception as err:
                exception = (
                    f"Unknown global exception: {err}, {err.args}, "
                    f"{''.join(traceback.format_exception(None, err, err.__traceback__))}"
                )
                self._logger.exception(exception)
                response = {MESSAGE_EXCEPTION: exception}

            self._logger.debug(
                f"got response at {time.perf_counter() - global_start} since start"
            )
            if WANT_PROFILING:
                profiler.disable()
                profiler.dump_stats("profile.log")
                profiler.enable()

            self._logger.debug(
                f"return response at {time.perf_counter() - global_start} since start"
            )
            self.manager_to_api_queue.put({uuid: response})

    def _handle_api_request(self) -> None:
        try:
            request = self.api_to_manager_queue.get(block=True, timeout=None)
            if isinstance(request, dict):
                now = time.perf_counter()
                self._logger.debug(
                    f"Handle content at {now - global_start} since start"
                )
                self._handle_content(request)
        except Empty:
            self._logger.debug("api_to_manager_queue was Empty.")
        except AttributeError:
            self._logger.exception(
                "Probably, api <-> manager queues are None."
            )

    def run(self) -> None:
        signal.signal(signal.SIGINT, self._graceful_shutdown)
        signal.signal(signal.SIGTERM, self._graceful_shutdown)

        while self.run_loop:
            self._handle_api_request()
            self._logger.info(f"Current time: {get_utc_now()}")

    def _graceful_shutdown(self, signum=None, frame=None) -> None:
        self.run_loop = False
        self.api_process.terminate()
        self.api_process.join()


def launch_api_server(
    queue: multiprocessing.Queue, return_queue: multiprocessing.Queue
) -> None:
    app.communicator = QueueCommunicator(queue, return_queue)
    uvicorn.run(app, host="0.0.0.0", port=API_PORT, log_level="debug")


if __name__ == "__main__":
    if WANT_PROFILING:
        profiler = cProfile.Profile()
        profiler.enable()

    manager = Manager()

    print("Manager exited")
    sys.exit(0)
