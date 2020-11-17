import json
import os

import requests

from lib.constants import (
    MESSAGE_ALLOW_LIST,
    MESSAGE_HAR,
    MESSAGE_HEADERS,
    MESSAGE_HTML,
    MESSAGE_URL,
)
from lib.timing import get_utc_now

WANT_ALL_SCRAPED_WEBSITES = True


def load_test_html():
    # FIXME: Remove this!!!
    if WANT_ALL_SCRAPED_WEBSITES:
        data_path = "/home/rcc/projects/WLO/oeh-search-etl/scraped"
    else:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        path = "/".join(dir_path.split("/")[:-1])
        data_path = path + "/testsuite/scraped"

    logs = [
        f
        for f in os.listdir(data_path)
        if os.path.isfile(os.path.join(data_path, f)) and ".log" in f
    ]

    for log in logs:
        print(log.center(40, "-"))
        with open(data_path + "/" + log, "r") as file:
            raw = json.load(file)

        html_content = raw["html"]
        headers = raw["headers"]
        raw_url = raw["url"]
        raw_cookies = raw["cookies"]
        har = raw["har"]
        yield raw_url, html_content, headers, raw_cookies, har


if __name__ == "__main__":
    allow_list = {
        "advertisement": True,
        "easy_privacy": True,
        "malicious_extensions": True,
        "extracted_links": True,
        "extract_from_files": True,
        "internet_explorer_tracker": True,
        "cookies_in_html": True,
        "fanboy_annoyance": True,
        "fanboy_notification": True,
        "fanboy_social_media": True,
        "anti_adblock": True,
        "easylist_germany": True,
        "easylist_adult": True,
        "paywall": True,
        "content_security_policy": True,
        "iframe_embeddable": True,
        "pop_up": True,
        "reg_wall": True,
        "log_in_out": True,
        "accessibility": True,
        "cookies": True,
    }

    extractor_url = "http://0.0.0.0:5057/extract_meta"

    result = {}

    result_filename = "result.json"
    try:
        os.remove(result_filename)
    except FileNotFoundError:
        pass

    for url, raw_html, header, raw_cookies, har in load_test_html():
        starting_extraction = get_utc_now()

        headers = {"Content-Type": "application/json"}

        # FIXME HTTP Code 422
        payload = {
            MESSAGE_HTML: raw_html,
            MESSAGE_HEADERS: header,
            MESSAGE_URL: url,
            MESSAGE_ALLOW_LIST: allow_list,
            MESSAGE_HAR: har,
        }
        response = requests.request(
            "POST", extractor_url, headers=headers, data=json.dumps(payload)
        )

        output = json.loads(response.content)
        output.update(
            {"time_for_extraction": get_utc_now() - starting_extraction}
        )

        result.update({url: output})

        with open("result.json", "w") as fp:
            json.dump(result, fp)

        # print(output)
        # print(output.keys())
        # print("meta: ", output["meta"])
