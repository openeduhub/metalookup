import json
import multiprocessing
import os
import time
from datetime import datetime
from queue import Empty

import requests
import uvicorn

from app.api import app
from app.communication import ProcessToDaemonCommunication


class Metadata:
    tag_list: list = []
    key: str = ""
    url: str = ""
    comment_symbol: str = ""

    def start(self, html_content: str = "") -> dict:
        print(f"Starting {self.__class__.__name__}")
        values = self._start(html_content=html_content)
        return {self.key: values}

    def _start(self, html_content: str) -> list:
        if self.tag_list:
            values = [ele for ele in self.tag_list if ele in html_content]
        else:
            values = []
        return values

    def __download_tag_list(self):
        result = requests.get(self.url)
        self.tag_list = result.text.split("\n")

    def __prepare_tag_list(self):
        if "" in self.tag_list:
            self.tag_list.remove("")

        if self.comment_symbol != "":
            self.tag_list = [x for x in self.tag_list if not x.startswith(self.comment_symbol)]

    def setup(self):
        """Child function."""
        if self.url != "":
            self.__download_tag_list()
        self.__prepare_tag_list()


class Advertisement(Metadata):
    url: str = "https://easylist.to/easylist/easylist.txt"
    key: str = "ads"
    comment_symbol = "!"


class Tracker(Metadata):
    url: str = "https://easylist.to/easylist/easyprivacy.txt"
    key: str = "tracker"
    comment_symbol = "!"


class IFrameEmbeddable(Metadata):
    url: str = ""
    tag_list = ["Content-Security-Policy"]
    key: str = "iframe_embeddable"
    comment_symbol = "!"

    def _start(self, html_content: str):
        values = super()._start(html_content=html_content)
        print(f"{self.tag_list}: {values}")
        if values == "DENY" or values == "SAMEORIGIN" or "ALLOW-FROM" in values:
            return False
        return True


class Manager:
    metadata_extractors: list = []

    def __init__(self):

        extractors = [Advertisement, Tracker, IFrameEmbeddable]
        for extractor in extractors:
            self.metadata_extractors.append(extractor())

        self.api_to_engine_queue = multiprocessing.Queue()
        self.engine_to_api_queue = multiprocessing.Queue()
        api_process = multiprocessing.Process(
            target=api_server, args=(self.api_to_engine_queue, self.engine_to_api_queue)
        )
        api_process.start()

        self.run()

    def get_api_request(self):
        if self.api_to_engine_queue is not None:
            try:
                request = self.api_to_engine_queue.get(block=False, timeout=0.1)
                if isinstance(request, dict):
                    self.handle_content(request)
            except Empty:
                pass

    def setup(self):
        for metadata_extractor in self.metadata_extractors:
            metadata_extractor: Metadata
            metadata_extractor.setup()

    def start(self, html_content: str):

        data = {}
        for metadata_extractor in self.metadata_extractors:
            extracted_metadata = metadata_extractor.start(html_content)
            data.update(extracted_metadata)

            print(f"Resulting data: {data}")
        return data

    # =========== CYCLE ============
    def run(self):

        while True:
            self.get_api_request()
            print(f"Current time: {datetime.utcnow().timestamp()}")
            time.sleep(1)

    def handle_content(self, request):

        print(f"request: {request}")
        for uuid, message in request.items():
            print(f"message: {message}")
            content = message["content"]

            result = self.start(content)
            valid = True
            error_count = 0
            response = {"valid": valid, "error_count": error_count, "result": result}

            self.engine_to_api_queue.put({uuid: response})


def load_test_html():
    data_path = "/home/rcc/projects/WLO/oeh-search-etl/scraped"

    logs = [f for f in os.listdir(data_path)
            if os.path.isfile(os.path.join(data_path, f)) and ".log" in f]

    log = logs[0]

    with open(data_path + "/" + log, "r") as file:
        raw = json.load(file)

    html_content = raw["html"]

    return html_content


def api_server(queue, return_queue):
    app.api_queue = ProcessToDaemonCommunication(queue, return_queue)
    uvicorn.run(app, host="0.0.0.0", port=5057, log_level="info")


if __name__ == '__main__':
    manager = Manager()

    raw_html = load_test_html()

    manager.setup()
    manager.start(html_content=raw_html)
