class Metadata:
    def extract(self):
        """Child function. Values remain None."""

    def start(self):
        print(f"Starting {self.__class__.__name__}")
        self._start()

    def _start(self):
        """Child function. Values remain None."""
        self.values = None

    def _setup(self):
        """Child function."""

    def __init__(self):
        self.tag = []
        self.tag_list = []
        self.key = None
        self.values = None

        self._setup()


class Advertisement(Metadata):
    def _setup(self):
        self.tag_list = "easylist.txt"
        self.key = "ads"

    def _start(self):
        self.values = "cool_value"


class Extractor:
    html: str = ""
    metadata_extractors: list = []

    def __init__(self):
        advertisement = Advertisement()
        self.metadata_extractors.append(advertisement)

    def setup(self, html: str):
        self.html = html

    def start(self):

        data = {}
        for metadata_extractor in self.metadata_extractors:
            metadata_extractor: Metadata
            metadata_extractor.start()
            if metadata_extractor.key:
                data.update({metadata_extractor.key: metadata_extractor.values})

        print(f"Resulting data: {data}")


if __name__ == '__main__':
    extractor = Extractor()

    extractor.setup(html="empty")
    extractor.start()
