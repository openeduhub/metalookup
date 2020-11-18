import json
import statistics

RESULT_FILE_PATH = (
    "/home/rcc/projects/WLO/oeh-search-meta/developer_tools/result.json"
)


def evaluator():
    with open(RESULT_FILE_PATH) as file:
        data = json.loads(file.read())

    evaluated_files = list(data.keys())
    found_cookies = []
    found_cookies_in_html = []
    total_time = []

    for url, values in data.items():
        if values["meta"]:
            if "cookies" in values["meta"] and values["meta"]["cookies"]:
                for cookie in values["meta"]["cookies"]["values"]:
                    found_cookies.append(cookie["name"])
            elif (
                "cookies_in_html" in values["meta"]
                and values["meta"]["cookies_in_html"]
            ):
                for cookie in values["meta"]["cookies_in_html"]["values"]:
                    found_cookies_in_html.append(cookie["name"])

        total_time.append(values["time_for_extraction"])

    print("summary".center(80, "-"))
    print("Number of evaluated files: ", len(evaluated_files))
    print("Uniquie cookies from splash: ", set(found_cookies))
    print("Uniquie cookies from html/easylist: ", set(found_cookies_in_html))

    if len(total_time) >= 2:
        print(
            f"Total extraction time: {sum(total_time)}s or "
            f"{sum(total_time) / len(evaluated_files)}"
            f"+-{statistics.stdev(total_time) / len(evaluated_files)}s per file."
        )
    else:
        print(
            f"Total extraction time: {sum(total_time)}s or {sum(total_time) / len(evaluated_files)}s per file."
        )


if __name__ == "__main__":
    evaluator()
