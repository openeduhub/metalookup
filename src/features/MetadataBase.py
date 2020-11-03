import re

import requests


class MetadataBase:
    tag_list: list = []
    tag_list_last_modified = ""
    tag_list_expires: int = 0
    key: str = ""
    url: str = ""
    comment_symbol: str = ""
    evaluate_header: bool = False

    def __init__(self, logger) -> None:
        self._logger = logger

    def start(self, html_content: str = "", header=None) -> dict:
        if header is None:
            header = {}
        self._logger.info(f"Starting {self.__class__.__name__}")
        values = self._start(html_content=html_content, header=header)
        return {self.key: {"values": values, "tag_list_last_modified": self.tag_list_last_modified,
                           "tag_list_expires": self.tag_list_expires}}

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

    def __download_tag_list(self) -> None:
        result = requests.get(self.url)
        if result.status_code == 200:
            self.tag_list = result.text.split("\n")
        else:
            self._logger.warning(f"Downloading tag list from '{self.url}' yielded status code '{result.status_code}'.")

    def __extract_date_from_list(self):
        expires_expression = re.compile(r"[!#:]\sExpires[:=]\s?(\d+)\s?\w{0,4}")
        last_modified_expression = re.compile(r"[!#]\sLast modified:\s(\d\d\s\w{3}\s\d{4}\s\d\d:\d\d\s\w{3})")
        for line in self.tag_list[0:10]:
            match = last_modified_expression.match(line)
            if match:
                self.tag_list_last_modified = match.group(1)

            match = expires_expression.match(line)
            if match:
                self.tag_list_expires = int(match.group(1))

            if self.tag_list_last_modified != "" and self.tag_list_expires != 0:
                break

    def __prepare_tag_list(self) -> None:
        self.tag_list = [i for i in self.tag_list if i != ""]

        if self.comment_symbol != "":
            self.tag_list = [x for x in self.tag_list if not x.startswith(self.comment_symbol)]

    def setup(self) -> None:
        """Child function."""
        if self.url != "":
            self.__download_tag_list()
            self.__extract_date_from_list()
            self.__prepare_tag_list()
