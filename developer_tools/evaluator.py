import json

RESULT_FILE_PATH = "../local_tools/tester/result.json"


def evaluator():
    with open(RESULT_FILE_PATH) as file:
        data = json.loads(file.read())

    evaluated_files = list(data.keys())
    found_cookies = []
    total_time = 0

    print(evaluated_files)
    for url, values in data.items():
        for cookie in values["cookies"]["values"]:
            found_cookies.append(cookie["name"])
        total_time += values["time_for_extraction"]
    print("Uniquie cookies: ", set(found_cookies))
    print("Total extraction time: ", total_time, "s")


if __name__ == "__main__":
    evaluator()
