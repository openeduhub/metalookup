import json
import os
import statistics

import altair as alt
import pandas as pd

DATAFRAME = "data.csv"

RESULT_FILE_PATH = (
    "/home/rcc/projects/WLO/oeh-search-meta/developer_tools/result.json"
)


def load_raw_data_and_save_to_dataframe():
    with open(RESULT_FILE_PATH) as file:
        raw_data = json.loads(file.read())

    meta_feature_keys = [
        "advertisement",
        "easy_privacy",
        "malicious_extensions",
        "extracted_links",
        "extract_from_files",
        "internet_explorer_tracker",
        "cookies_in_html",
        "fanboy_annoyance",
        "fanboy_notification",
        "fanboy_social_media",
        "anti_adblock",
        "easylist_germany",
        "easylist_adult",
        "paywall",
        "content_security_policy",
        "iframe_embeddable",
        "pop_up",
        "reg_wall",
        "log_in_out",
        "accessibility",
        "cookies",
        "g_d_p_r",
    ]
    row_names = ["values", "probability", "decision"]
    col_names = []

    for key in meta_feature_keys:
        for row_name in row_names:
            col_names.append(f"{key}.{row_name}")

    col_names += ["time_until_complete", "time_for_extraction", "exception"]

    print(col_names)

    data = pd.DataFrame(columns=col_names)

    for url, elements in raw_data.items():
        row = []
        for meta_key in meta_feature_keys:
            if (
                    elements["meta"] is not None
                    and meta_key in elements["meta"].keys()
                    and elements["meta"][meta_key] is not None
            ):
                for row_name in row_names:
                    if row_name in elements["meta"][meta_key]:
                        row.append(elements["meta"][meta_key][row_name])
                    else:
                        row.append(None)
            else:
                [row.append(None) for _ in row_names]

        row.append(elements["time_until_complete"])
        row.append(elements["time_for_extraction"])
        row.append(elements["exception"])
        # print(row)
        data.loc[url] = row

    data.to_csv(DATAFRAME)


def evaluator():
    if not os.path.isfile(DATAFRAME):
        print(f"{DATAFRAME} does not exist, reading raw data.")
        load_raw_data_and_save_to_dataframe()

    print(f"Loading data from {DATAFRAME}.")
    df = pd.read_csv(DATAFRAME, index_col=0)
    print(df.columns)

    if len(df) > 0:
        print("summary".center(80, "-"))
        print("Number of evaluated files: ", len(df))

        total_time = df["time_for_extraction"].sum()
        print(
            f"Total extraction time: {total_time}s or "
            f"{total_time / len(df)}"
            f"+-{statistics.stdev(df['time_for_extraction']) / len(df)}s per file."
        )
    failed_evaluations = {}

    # Get rows with none content
    print("Failing evaluations".center(80, "-"))
    rslt_df = df[df["advertisement.values"].isnull()]
    print(f"Total urls with failing evaluation: {len(rslt_df)}")
    failed_evaluations.update({"nan_evaluation": rslt_df.index.values})

    print("Unique GDPR values".center(80, "-"))
    gdpr_values = df["g_d_p_r.values"].unique()
    unique_values = []
    for row in gdpr_values:
        if isinstance(row, str):
            row = (
                row.replace("'", "")
                    .replace("[", "")
                    .replace("]", "")
                    .split(", ")
            )
            unique_values += [
                element for element in row if element not in unique_values
            ]
    print(f"Unique values in GDPR: {unique_values}")

    rslt_df = df[df["accessibility.probability"] < 0]
    print(f"Total urls with failing accessibility: {len(rslt_df)}")
    failed_evaluations.update({"negative_accessibility": rslt_df.index.values})

    source = df.loc[:, "time_for_extraction"]

    df.insert(0, "x", range(0, len(source)))
    df.insert(0, "accessibility", df["accessibility.probability"])

    chart1 = (
        alt.Chart(df)
            .mark_circle(size=60)
            .encode(
            x="x:Q",
            y="accessibility:Q",
        )
            .interactive()
    )

    chart2 = (
        alt.Chart(df, title="This is the Chart Title")
            .mark_circle(size=60)
            .encode(
            x="x:Q",
            y="time_for_extraction:Q",
        )
            .interactive()
    )

    chart3 = (
        alt.Chart(df, title="This is the Chart Title")
            .mark_circle(size=60)
            .encode(
            x="x:Q",
            y="accessibility.probability:Q",
        )
            .interactive()
    )
    print(failed_evaluations)

    (chart1 | chart2 | chart3).show()


if __name__ == "__main__":
    evaluator()
