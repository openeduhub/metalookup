import json
import os

import requests


class Metadata:
    tag_list: list = []
    key: str = ""

    def start(self, html_content: str = "") -> dict:
        print(f"Starting {self.__class__.__name__}")
        values = self._start(html_content=html_content)
        return {self.key: values}

    def _start(self, html_content: str) -> list:
        if self.tag_list:
            values = [ele for ele in self.tag_list if (ele in html_content)]
        else:
            values = []
        return values

    def setup(self):
        """Child function."""


class Advertisement(Metadata):
    url: str = "https://easylist.to/easylist/easylist.txt"
    key: str = "ads"

    def __download_tag_list(self):
        myfile = requests.get(self.url)
        self.tag_list = myfile.text.split("\n")

    def __prepare_tag_list(self):
        if "" in self.tag_list:
            self.tag_list.remove("")

        comment_symbol = "!"
        self.tag_list = [x for x in self.tag_list if not x.startswith(comment_symbol)]

    def setup(self):
        self.__download_tag_list()
        self.__prepare_tag_list()


class Tracker(Metadata):
    url: str = "https://easylist.to/easylist/easyprivacy.txt"
    key: str = "ads"

    def __download_tag_list(self):
        myfile = requests.get(self.url)
        self.tag_list = myfile.text.split("\n")

    def __prepare_tag_list(self):
        if "" in self.tag_list:
            self.tag_list.remove("")

        comment_symbol = "!"
        self.tag_list = [x for x in self.tag_list if not x.startswith(comment_symbol)]

    def setup(self):
        self.__download_tag_list()
        self.__prepare_tag_list()


class Extractor:
    metadata_extractors: list = []

    def __init__(self):
        advertisement = Advertisement()
        self.metadata_extractors.append(advertisement)

        tracker = Tracker()
        self.metadata_extractors.append(tracker)

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


def load_test_html():
    data_path = "/home/rcc/projects/WLO/oeh-search-etl/scraped"

    logs = [f for f in os.listdir(data_path) if os.path.isfile(os.path.join(data_path, f)) and ".log" in f]

    log = logs[0]

    with open(data_path + "/" + log, "r") as file:
        raw = json.load(file)

    html_content = raw["html"]

    return html_content


if __name__ == '__main__':
    extractor = Extractor()

    raw_html = load_test_html()

    extractor.setup()
    extractor.start(html_content=raw_html)
