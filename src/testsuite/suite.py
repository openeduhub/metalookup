import json
import os
from urllib.parse import urlparse

import requests

URLS = ["https://www.dictionary.com/"]


def main():
    """
    Download specific websites for testing purpose and store them locally

    :return:
    """
    for url in URLS:
        response = requests.get(url)

        domain = urlparse(url).netloc
        filename = domain.replace(".", "_")

        dir_path = os.path.dirname(os.path.realpath(__file__))

        path = "/".join(dir_path.split("/")[:-2])
        for path_elements in ["/local_tools", "/testsuite", "/scraped/"]:
            path += path_elements
            try:
                os.mkdir(path)
            except FileExistsError:
                pass

        data = {}
        data.update({"html": str(response.content)})
        data.update({"headers": str(response.headers)})
        data.update({"url": str(response.url)})

        data.update({"json": str(response.json)})
        data.update({"cookies": str(response.cookies)})

        with open(path + filename + ".log", "w") as file:
            file.write(json.dumps(data))


if __name__ == "__main__":
    main()
