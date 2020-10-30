import json
import os

import requests


class Metadata:
    tag: str = ""
    tag_list: list = []
    key: str = ""
    values: list = []

    def start(self, html_content: str = ""):
        print(f"Starting {self.__class__.__name__}")
        self._start(html_content=html_content)

    def _start(self, html_content: str):
        if not self.tag_list and not self.tag:
            self.values = []
        elif self.tag_list and not self.tag:
            self.values = [ele for ele in self.tag_list if (ele in html_content)]
        else:
            self.values = []
        return self.values

    def setup(self):
        """Child function."""


class Advertisement(Metadata):
    url: str = ""

    def setup(self):
        # TODO: Split
        # Setup
        self.url = 'https://easylist.to/easylist/easylist.txt'

        # I/O
        myfile = requests.get(self.url)
        self.tag_list = myfile.text.split("\n")

        # DATA Operation
        # TODO: Split
        if "" in self.tag_list:
            self.tag_list.remove("")

        comments = "!"
        self.tag_list = [x for x in self.tag_list if not x.startswith(comments)]

        self.key = "ads"


class Extractor:
    metadata_extractors: list = []

    def __init__(self):
        advertisement = Advertisement()
        self.metadata_extractors.append(advertisement)

    def setup(self):
        for metadata_extractor in self.metadata_extractors:
            metadata_extractor: Metadata
            metadata_extractor.setup()

    def start(self, html_content: str):

        data = {}
        for metadata_extractor in self.metadata_extractors:
            metadata_extractor: Metadata
            metadata_extractor.start(html_content)
            if metadata_extractor.key:
                data.update({metadata_extractor.key: metadata_extractor.values})

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
