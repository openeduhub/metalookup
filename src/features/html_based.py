from metadata import Metadata


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
        self._logger.debug(f"{self.tag_list}: {values}")
        if values == "DENY" or values == "SAMEORIGIN" or "ALLOW-FROM" in values:
            return False
        return True
