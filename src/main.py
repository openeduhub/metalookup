import json
import os

import requests


class Metadata:
    def extract(self):
        """Child function. Values remain None."""

    def start(self):
        print(f"Starting {self.__class__.__name__}")
        self._start()

    def _start(self):
        """Child function. Values remain None."""
        if not self.tag_list and not self.tag:
            self.values = None
        elif self.tag_list and not self.tag:
            self.values = [ele for ele in self.tag_list if (ele in self.html)]
        else:
            self.values = None
        return self.values

    def _setup(self, html: str):
        """Child function."""
        self.html = html

    def __init__(self):
        self.tag: str = ""
        self.tag_list: list = []
        self.key: str = None
        self.values: list = []
        self.html = ""


class Advertisement(Metadata):
    def _setup(self, html):
        super()._setup(html=html)

        # I/O
        # TODO: Split
        self.url = 'https://easylist.to/easylist/easylist.txt'
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
    html: str = ""
    metadata_extractors: list = []

    def __init__(self):
        advertisement = Advertisement()
        self.metadata_extractors.append(advertisement)

    def setup(self, html: str):
        for metadata_extractor in self.metadata_extractors:
            metadata_extractor: Metadata
            metadata_extractor._setup(html)

    def start(self):

        data = {}
        for metadata_extractor in self.metadata_extractors:
            metadata_extractor: Metadata
            metadata_extractor.start()
            if metadata_extractor.key:
                data.update({metadata_extractor.key: metadata_extractor.values})

        print(f"Resulting data: {data}")


def load_test_html():
    DATA_PATH = "/home/rcc/projects/WLO/oeh-search-etl/scraped"

    logs = [f for f in os.listdir(DATA_PATH) if os.path.isfile(os.path.join(DATA_PATH, f)) and ".log" in f]

    log = logs[0]

    with open(DATA_PATH + "/" + log, "r") as file:
        raw = json.load(file)

    html = raw["html"]

    return html


if __name__ == '__main__':
    extractor = Extractor()

    html = load_test_html()

    extractor.setup(html=html)
    extractor.start()
