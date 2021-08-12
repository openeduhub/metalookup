import json
import sys

import requests

from lib.constants import MESSAGE_EXCEPTION, MESSAGE_URL, SECONDS_PER_DAY
from lib.settings import METALOOKUP_EXTRACT_META, METALOOKUP_RECORDS
from lib.timing import get_utc_now
from lib.tools import get_unique_list


def main(maximum_age_in_seconds: int = SECONDS_PER_DAY):

    payload = {}
    headers = {}

    response = requests.request(
        "GET", METALOOKUP_RECORDS, headers=headers, data=payload
    )

    try:
        records = json.loads(response.text)["records"]
    except TypeError as err:
        print(
            f"Exception when loading records with {err.args}.\nPotentially due to outdated record schema. "
        )
        sys.exit(1)

    print(
        f"----------------- Total number of evaluated records so far: {len(records)}"
    )
    if len(records) == 1:
        print(records)
        return

    unique_urls = []
    for record in records:
        if (
            record[MESSAGE_EXCEPTION] != ""
            and "splash" in record[MESSAGE_EXCEPTION]
            and record["timestamp"] < (get_utc_now() - maximum_age_in_seconds)
        ):
            unique_urls.append(record[MESSAGE_URL])

    output = "\n".join(get_unique_list(unique_urls))
    print(
        f"----------------- Unique evaluated urls with splash error:\n{output}"
    )

    headers = {"Content-Type": "application/json"}

    for url_to_rerun in get_unique_list(unique_urls):
        print(f"Working on {url_to_rerun}")
        payload = {
            MESSAGE_URL: url_to_rerun,
            "debug": True,
        }
        requests.request(
            "POST",
            METALOOKUP_EXTRACT_META,
            headers=headers,
            data=json.dumps(payload),
        )


if __name__ == "__main__":
    main()
