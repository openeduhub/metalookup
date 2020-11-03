import requests


class Metadata:
    tag_list: list = []
    key: str = ""
    url: str = ""
    comment_symbol: str = ""
    evaluate_header: bool = False

    def __init__(self, logger):
        self._logger = logger

    def start(self, html_content: str = "", header=None) -> dict:
        if header is None:
            header = {}
        self._logger.info(f"Starting {self.__class__.__name__}")
        values = self._start(html_content=html_content, header=header)
        return {self.key: values}

    def _start(self, html_content: str, header: dict) -> list:
        if self.evaluate_header:
            if len(self.tag_list) == 1:
                values = header[self.tag_list[0]] if self.tag_list[0] in header else ""
            else:
                values = [header[ele] for ele in self.tag_list if ele in header]
        else:
            if self.tag_list:
                values = [ele for ele in self.tag_list if ele in html_content]
            else:
                values = []
        return values

    def __download_tag_list(self):
        result = requests.get(self.url)
        if result.status_code == 200:
            self.tag_list = result.text.split("\n")

    def __prepare_tag_list(self):
        self.tag_list = [i for i in self.tag_list if i != ""]

        if self.comment_symbol != "":
            self.tag_list = [x for x in self.tag_list if not x.startswith(self.comment_symbol)]

    def setup(self):
        """Child function."""
        if self.url != "":
            self.__download_tag_list()
        self.__prepare_tag_list()
