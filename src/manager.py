import logging
import multiprocessing
import os
import time
from datetime import datetime
from logging import handlers
from queue import Empty

import uvicorn

from app.api import app
from app.communication import ProcessToDaemonCommunication
from metadata import Metadata
from features.html_based import Advertisement, Tracker, IFrameEmbeddable
from settings import API_PORT, LOG_LEVEL, LOG_PATH


class Manager:
    metadata_extractors: list = []

    def __init__(self):

        self._create_logger()

        self._create_extractors()

        self._create_api()

        self.run()

    def _create_api(self):
        self.api_to_manager_queue = multiprocessing.Queue()
        self.manager_to_api_queue = multiprocessing.Queue()
        api_process = multiprocessing.Process(
            target=api_server, args=(self.api_to_manager_queue, self.manager_to_api_queue)
        )
        api_process.start()

    def _create_extractors(self):
        extractors = [Advertisement, Tracker, IFrameEmbeddable]
        for extractor in extractors:
            self.metadata_extractors.append(extractor(self._logger))

    def _create_logger(self):
        self._logger = logging.getLogger(name="manager")

        self._logger.propagate = True

        self._logger.setLevel(LOG_LEVEL)

        formatter = logging.Formatter("%(asctime)s  %(levelname)-7s %(message)s")

        # Convert time to UTC/GMT time
        logging.Formatter.converter = time.gmtime

        # standard log
        dir_path = os.path.dirname(os.path.realpath(__file__))
        print(f"dir_path: {dir_path}")

        data_path = dir_path + "/" + LOG_PATH

        log_15_mb_limit = 1024 * 1024 * 15
        backup_count = 10000

        if not os.path.exists(data_path):
            os.mkdir(data_path, mode=0o755)
        fh = handlers.RotatingFileHandler(filename=f"{data_path}/manager.log", maxBytes=log_15_mb_limit,
                                          backupCount=backup_count)

        fh.setLevel(LOG_LEVEL)
        fh.setFormatter(formatter)

        self._logger.addHandler(fh)

    def get_api_request(self):
        if self.api_to_manager_queue is not None:
            try:
                request = self.api_to_manager_queue.get(block=False, timeout=0.1)
                if isinstance(request, dict):
                    self.handle_content(request)
            except Empty:
                pass

    def setup(self):
        for metadata_extractor in self.metadata_extractors:
            metadata_extractor: Metadata
            metadata_extractor.setup()

    def _extract_meta_data(self, html_content: str):

        data = {}
        for metadata_extractor in self.metadata_extractors:
            extracted_metadata = metadata_extractor.start(html_content)
            data.update(extracted_metadata)

            self._logger.debug(f"Resulting data: {data}")
        return data

    # =========== CYCLE ============
    def run(self):

        while True:
            self.get_api_request()
            self._logger.info(f"Current time: {datetime.utcnow().timestamp()}")
            time.sleep(1)

    def handle_content(self, request):

        self._logger.debug(f"request: {request}")
        for uuid, message in request.items():
            self._logger.debug(f"message: {message}")
            content = message["content"]

            meta_data = self._extract_meta_data(content)

            response = meta_data
            self.manager_to_api_queue.put({uuid: response})


def api_server(queue, return_queue):
    app.api_queue = ProcessToDaemonCommunication(queue, return_queue)
    uvicorn.run(app, host="0.0.0.0", port=API_PORT, log_level="info")


if __name__ == '__main__':
    manager = Manager()
