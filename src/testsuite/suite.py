import json

import requests
from urllib.parse import urlparse

urls = ["https://www.dictionary.com/"]

# Making a get request
for url in urls:
    response = requests.get(url)

    domain = urlparse(url).netloc
    filename = domain.replace(".", "_")

    path = "/home/rcc/projects/WLO/oeh-search-etl/scraped/"

    with open(path + filename + ".log", "w") as file:
        data = {}
        data.update({"html": str(response.content)})
        data.update({"headers": str(response.headers)})
        data.update({"url": str(response.url)})

        data.update({"json": str(response.json)})
        data.update({"cookies": str(response.cookies)})

        file.write(json.dumps(data))
