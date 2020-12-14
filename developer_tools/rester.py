import json
import os
import time
from json.decoder import JSONDecodeError

import requests

from developer_tools.evaluator import RESULT_FILE_PATH
from lib.constants import (
    MESSAGE_ALLOW_LIST,
    MESSAGE_HAR,
    MESSAGE_HEADERS,
    MESSAGE_HTML,
    MESSAGE_URL,
)
from lib.timing import get_utc_now


def load_file_list():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    path = "/".join(dir_path.split("/")[:-1])
    data_path = path + "/scraped"

    files = [
        f
        for f in os.listdir(data_path)
        if os.path.isfile(os.path.join(data_path, f)) and ".log" in f
    ]
    return files, data_path


def load_scraped_data(logs: list, data_path: str):
    for log in logs:
        with open(data_path + "/" + log, "r") as file:
            try:
                raw = json.load(file)
            except JSONDecodeError as e:
                print(f"File '{file}' cannot be evaluated: {e.args}")
                continue
        yield raw


def rester():
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
        "g_d_p_r": True,
        "javascript": True,
    }

    extractor_url = "http://0.0.0.0:5057/extract_meta"

    result = {}

    try:
        os.remove(RESULT_FILE_PATH)
    except FileNotFoundError:
        pass

    logs, file_path = load_file_list()
    for counter, raw in enumerate(load_scraped_data(logs, file_path)):
        before = time.perf_counter()
        print(f"Working file {counter + 1} of {len(logs)}".center(80, "-"))
        print(raw["url"])

        starting_extraction = get_utc_now()

        headers = {"Content-Type": "application/json"}

        payload = {
            MESSAGE_HTML: raw["html"],
            MESSAGE_HEADERS: raw["headers"],
            MESSAGE_URL: raw["url"],
            MESSAGE_ALLOW_LIST: allow_list,
            MESSAGE_HAR: raw["har"],
            "debug": True,
        }
        response = requests.request(
            "POST", extractor_url, headers=headers, data=json.dumps(payload)
        )

        try:
            output = json.loads(response.content)
        except JSONDecodeError as e:
            print(response.content)
            print(f"Exception: {e}, {e.args}")
            output = {}
        output.update(
            {"time_for_extraction": get_utc_now() - starting_extraction}
        )

        result.update({raw["url"]: output})

        with open(RESULT_FILE_PATH, "w") as fp:
            json.dump(result, fp)

        print(output)
        after = time.perf_counter()
        print(f"Total time needed in series: {after - before}")


if __name__ == "__main__":
    rester()
