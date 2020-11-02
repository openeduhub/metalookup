import requests


class Metadata:
    tag_list: list = []
    key: str = ""
    url: str = ""
    comment_symbol: str = ""

    def __init__(self, logger):
        self._logger = logger

    def start(self, html_content: str = "") -> dict:
        self._logger.info(f"Starting {self.__class__.__name__}")
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
