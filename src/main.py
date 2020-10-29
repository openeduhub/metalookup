class Metadatum:
    def extract(self):
        pass

    def start(self):
        print(f"Starting {self.__class__.__name__}")
        self.values = "cool_value"

    def __init__(self):
        self.tag = []
        self.tag_list = []
        self.key = None
        self.values = None


class Extractor:
    html: str = ""
    metadata_extractors: list = []

    def __init__(self):
        advertisment = Metadatum()
        advertisment.tag_list = "easylist.txt"
        advertisment.key = "ads"
        self.metadata_extractors.append(advertisment)

    def setup(self, html: str):
        self.html = html

    def start(self):

        data = {}
        for metadata_extractor in self.metadata_extractors:
            metadata_extractor.start()
            if metadata_extractor.key:
                data.update({metadata_extractor.key: metadata_extractor.values})

        print(f"data: {data}")


if __name__ == '__main__':
    extractor = Extractor()

    extractor.setup(html="empty")
    extractor.start()
