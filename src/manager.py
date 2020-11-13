import logging
import multiprocessing
import os
import signal
import time
from logging import handlers
from queue import Empty

import uvicorn

from app.api import app
from app.communication import ProcessToDaemonCommunication
from config_manager import ConfigManager
from features.extract_from_document import ExtractFromFiles
from features.html_based import (
    Advertisement,
    AntiAdBlock,
    ContentSecurityPolicy,
    Cookies,
    EasylistAdult,
    EasylistGermany,
    EasyPrivacy,
    FanboyAnnoyance,
    FanboyNotification,
    FanboySocialMedia,
    IETracker,
    IFrameEmbeddable,
    Paywalls,
    PopUp,
)
from features.malicious_extensions import MaliciousExtensions
from features.metadata_base import MetadataBase
from features.website_manager import WebsiteManager
from lib.constants import (
    LOGFILE_MANAGER,
    MESSAGE_ALLOW_LIST,
    MESSAGE_EXCEPTION,
    MESSAGE_HEADERS,
    MESSAGE_HTML,
    MESSAGE_META,
    MESSAGE_URL,
)
from lib.settings import API_PORT, LOG_LEVEL, LOG_PATH
from lib.timing import get_utc_now


class Manager:
    metadata_extractors: list = []
    run_loop: bool = False

    def __init__(self):

        self._create_logger()

        self._create_extractors()

        self._create_api()

        self.setup()

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

    def _create_extractors(self):

        extractors = [
            Advertisement,
            EasyPrivacy,
            MaliciousExtensions,
            ExtractFromFiles,
            IETracker,
            Cookies,
            FanboyAnnoyance,
            FanboyNotification,
            FanboySocialMedia,
            AntiAdBlock,
            EasylistGermany,
            EasylistAdult,
            Paywalls,
            ContentSecurityPolicy,
            IFrameEmbeddable,
            PopUp,
        ]

        for extractor in extractors:
            self.metadata_extractors.append(extractor(self._logger))

    def _create_logger(self):
        self._logger = logging.getLogger(name=LOGFILE_MANAGER)

        self._logger.propagate = True

        self._logger.setLevel(LOG_LEVEL)

        formatter = logging.Formatter(
            "%(asctime)s  %(levelname)-7s %(message)s"
        )

        # Convert time to UTC/GMT time
        logging.Formatter.converter = time.gmtime

        # standard log
        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_path = dir_path + "/" + LOG_PATH

        log_15_mb_limit = 1024 * 1024 * 15
        backup_count = 10000

        if not os.path.exists(data_path):
            os.mkdir(data_path, mode=0o755)

        fh = handlers.RotatingFileHandler(
            filename=f"{data_path}/{LOGFILE_MANAGER}.log",
            maxBytes=log_15_mb_limit,
            backupCount=backup_count,
        )

        fh.setLevel(LOG_LEVEL)
        fh.setFormatter(formatter)

        # error log
        error_handler = handlers.RotatingFileHandler(
            filename=f"{data_path}/{LOGFILE_MANAGER}_error.log",
            maxBytes=log_15_mb_limit,
            backupCount=backup_count,
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)

        self._logger.addHandler(fh)
        self._logger.addHandler(error_handler)

    def setup(self):
        for metadata_extractor in self.metadata_extractors:
            metadata_extractor: MetadataBase
            metadata_extractor.setup()

    # =========== LOOP ============

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

    def _extract_meta_data(
        self, allow_list: dict, config_manager: ConfigManager
    ) -> dict:
        data = {}
        for metadata_extractor in self.metadata_extractors:
            if allow_list[metadata_extractor.key]:
                if (
                    config_manager.is_host_predefined()
                    and config_manager.is_metadata_predefined(
                        metadata_extractor.key
                    )
                ):
                    extracted_metadata = (
                        config_manager.get_predefined_metadata(
                            metadata_extractor.key
                        )
                    )
                else:
                    extracted_metadata = metadata_extractor.start()

                data.update(extracted_metadata)
                self._logger.debug(f"Resulting data: {data}")
        return data

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
                website_manager = WebsiteManager.get_instance()
                website_manager.load_raw_data(
                    url=message[MESSAGE_URL],
                    html_content=message[MESSAGE_HTML],
                    raw_header=message[MESSAGE_HEADERS],
                )

                config_manager = ConfigManager.get_instance()
                config_manager.top_level_domain = (
                    website_manager.website_data.top_level_domain
                )

                starting_extraction = get_utc_now()
                try:
                    extracted_meta_data = self._extract_meta_data(
                        message[MESSAGE_ALLOW_LIST], config_manager
                    )
                except Exception as e:
                    self._logger.error(
                        f"Extracting metadata raised: '{e.args}'",
                        exc_info=True,
                    )
                    extracted_meta_data = {}

                extracted_meta_data.update(
                    {
                        "time_for_extraction": get_utc_now()
                        - starting_extraction,
                        **website_manager.get_website_data_to_log(),
                    }
                )

                response = extracted_meta_data
                website_manager.reset()

            self.manager_to_api_queue.put({uuid: response})

    def _graceful_shutdown(self, signum=None, frame=None):
        self.run_loop = False


def api_server(queue, return_queue):
    app.api_queue = ProcessToDaemonCommunication(queue, return_queue)
    uvicorn.run(app, host="0.0.0.0", port=API_PORT, log_level="info")


if __name__ == "__main__":
    manager = Manager()
