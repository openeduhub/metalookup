import json
import os
import re
import statistics

import altair as alt
import numpy as np
import pandas as pd
from tldextract import TLDExtract

from lib.constants import MESSAGE_META

DATAFRAME = "data.csv"

RESULT_FILE_PATH = "result.json"


def load_raw_data_and_save_to_dataframe():
    with open(RESULT_FILE_PATH) as file:
        raw_data = json.loads(file.read())

    meta_feature_keys = [
        "advertisement",
        "easy_privacy",
        "malicious_extensions",
        "extracted_links",
        "extract_from_files",
        "cookies_in_html",
        "fanboy_annoyance",
        "fanboy_notification",
        "fanboy_social_media",
        "anti_adblock",
        "easylist_germany",
        "easylist_adult",
        "paywall",
        "security",
        "iframe_embeddable",
        "pop_up",
        "reg_wall",
        "log_in_out",
        "accessibility",
        "cookies",
        "g_d_p_r",
    ]
    row_names = ["values", "probability", "isHappyCase", "time_for_completion"]
    col_names = [
        f"{key}.{row_name}"
        for row_name in row_names
        for key in meta_feature_keys
    ]

    col_names.extend(
        ["time_until_complete", "time_for_extraction", "exception"]
    )

    print("col_names")
    print(col_names)

    data = pd.DataFrame(columns=col_names)

    for url, elements in raw_data.items():
        row = []
        for meta_key in meta_feature_keys:
            if (
                elements[MESSAGE_META] is not None
                and meta_key in elements[MESSAGE_META].keys()
                and elements[MESSAGE_META][meta_key] is not None
            ):
                for row_name in row_names:
                    if row_name in elements[MESSAGE_META][meta_key]:
                        row.append(elements[MESSAGE_META][meta_key][row_name])
                    else:
                        row.append(None)
            else:
                _ = [row.append(None) for _ in row_names]

        row.append(elements["time_until_complete"])
        row.append(elements["time_for_extraction"])
        row.append(elements["exception"])
        data.loc[url, :] = row

    data.to_csv(DATAFRAME)


def regex_cookie_parameter(cookie: str, parameter: str = "name"):
    regex = re.compile(fr"'{parameter}':\s'(.*?)',")
    matches = []
    if not isinstance(cookie, float):
        matches = regex.findall(cookie)
    return matches


def evaluator(want_details: bool = False):
    if not os.path.isfile(DATAFRAME):
        print(f"{DATAFRAME} does not exist, reading raw data.")
        load_raw_data_and_save_to_dataframe()

    print(f"Loading data from {DATAFRAME}.")
    df = pd.read_csv(DATAFRAME, index_col=0)
    if want_details:
        print(df.columns)

    if len(df) > 0:
        print("summary".center(80, "-"))
        print("Number of evaluated files: ", len(df))

        total_time = df.loc[:, "time_for_extraction"].sum()

        if len(df) > 1:
            var = statistics.stdev(df.loc[:, "time_for_extraction"])
        else:
            var = 0

        print(
            f"Total extraction time: {total_time}s or "
            f"{total_time / len(df)}"
            f"+-{var / len(df)}s per file."
        )
    failed_evaluations = {}

    # Get rows with none content
    print("Failing evaluations".center(80, "-"))
    rslt_df = df[df.loc[:, "advertisement.values"].isnull()]
    print(f"Total urls with failing evaluation: {len(rslt_df)}")
    failed_evaluations.update({"nan_evaluation": rslt_df.index.values})

    print("Unique GDPR values".center(80, "-"))
    gdpr_values = df.loc[:, "g_d_p_r.values"].unique()
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

    rslt_df = df[df.loc[:, "accessibility.probability"] < 0]
    failed_evaluations.update({"negative_accessibility": rslt_df.index.values})

    source = df.loc[:, "time_for_extraction"]

    df.insert(0, "x", range(0, len(source)))
    df.insert(0, "accessibility", df.loc[:, "accessibility.probability"])
    df.insert(0, "found_ads", df.loc[:, "advertisement.probability"])

    print(
        f"Total urls with negative accessibility: {len(failed_evaluations['negative_accessibility'])}"
    )
    print(
        f"Total urls with NaN in evaluation results: {len(failed_evaluations['nan_evaluation'])}"
    )

    # Cookie
    cookies_values = "cookies.values"
    cookies_df = df.apply(
        lambda df_row: regex_cookie_parameter(df_row[cookies_values]), axis=1
    ).tolist()
    cookies_df = set(item for subl in cookies_df for item in subl)
    print("Unique cookies".center(120, "-"))
    print(cookies_df)

    # Domain
    domains = df.apply(
        lambda df_row: regex_cookie_parameter(
            df_row[cookies_values], parameter="domain"
        ),
        axis=1,
    ).tolist()
    domains = set(item for subl in domains for item in subl if item != "")
    print("Unique domains".center(120, "-"))
    print(domains)

    # Ads

    parameters = ["advertisement", "easy_privacy", "easylist_germany"]
    for parameter in parameters:
        ads = df.loc[:, f"{parameter}.values"].tolist()
        ads = [ad.split(", ") for ad in ads if isinstance(ad, str)]
        ads = set(
            item.replace("'", "").replace("[", "").replace("]", "")
            for sub in ads
            for item in sub
        )
        print(f"{len(ads)} unique values for {parameter}".center(120, "-"))
        if want_details:
            print(ads)

    # Top level domains
    extractor = TLDExtract(cache_dir=False)

    df.insert(
        0,
        "domain",
        df.apply(lambda df_row: extractor(df_row.name).domain, axis=1),
    )
    print("Unique top level domains".center(120, "-"))
    top_level_domains = df.loc[:, "domain"]
    print(top_level_domains.unique())

    # Extensions
    extract_from_files_values = "extract_from_files.values"
    file_extensions = [
        os.path.splitext(link)[-1]
        if not (link == [] or isinstance(link, float))
        else []
        for link in df.loc[:, extract_from_files_values]
    ]
    file_extensions = set(x for x in file_extensions if x not in ([], ""))
    print("Unique file extensions".center(120, "-"))
    print(file_extensions)

    df.insert(
        0, "time_difference", df.loc[:, "time_for_extraction"].copy(deep=True)
    )

    # extract time_for_completion
    performance_columns = ["key", "average", "std", "domain"]
    metadata_performance = pd.DataFrame({}, columns=performance_columns)
    for column in df.columns:
        if len(elements := column.split(".")) == 2:
            key = elements[0]
            parameter = elements[1]
            if parameter == "time_for_completion":
                for host in top_level_domains.unique():
                    mask = df.loc[:, "domain"] == host
                    values = df.loc[mask, column]

                    if sum(~np.isnan(values)) > 0:
                        data = {
                            "key": key,
                            "average": np.nanmean(values),
                            "std": np.nanstd(values),
                            "min": np.nanmin(values),
                            "max": np.nanmax(values),
                            "domain": host,
                        }
                    else:
                        data = {
                            "key": key,
                            "average": np.NaN,
                            "std": np.NaN,
                            "min": np.NaN,
                            "max": np.NaN,
                            "domain": host,
                        }

                    metadata_performance = metadata_performance.append(
                        pd.Series(
                            data=data,
                            name=key,
                        )
                    )
                df.loc[:, "time_difference"] = df.loc[
                    :, "time_difference"
                ].sub(df[column], fill_value=0)

    # Plotting
    fig_width = 500
    fig_height = 300

    chart1 = (
        alt.Chart(df)
        .mark_circle(size=60)
        .encode(x="x:Q", y="accessibility:Q", color=alt.Color("domain"))
        .interactive()
        .properties(width=fig_width, height=fig_height)
    )

    chart2 = (
        alt.Chart(df, title="")
        .mark_circle(size=60)
        .encode(x="x:Q", y="time_for_extraction:Q", color=alt.Color("domain"))
        .interactive()
        .properties(width=fig_width, height=fig_height)
    )

    chart3 = (
        alt.Chart(df, title="")
        .mark_circle(size=60)
        .encode(x="x:Q", y="found_ads:Q", color=alt.Color("domain"))
        .interactive()
        .properties(width=fig_width, height=fig_height)
    )

    min_value = (
        alt.Chart(metadata_performance)
        .mark_line()
        .encode(
            x="key:O",
            y=alt.Y(
                field="min",
                scale=alt.Scale(type="log"),
                type="quantitative",
                title="average [s]",
            ),
            color=alt.Color("domain"),
            strokeDash="domain",
        )
        .properties(width=fig_width, height=fig_height)
    )
    max_value = (
        alt.Chart(metadata_performance)
        .mark_line()
        .encode(
            x="key:O",
            y=alt.Y(
                field="max",
                scale=alt.Scale(type="log"),
                type="quantitative",
                title="average [s]",
            ),
            color=alt.Color("domain"),
            strokeDash="domain",
        )
        .properties(width=fig_width, height=fig_height)
    )

    performance_monitor = (
        max_value
        + min_value
        + (
            alt.Chart(metadata_performance, title="Time per metadatum")
            .mark_circle(size=60)
            .encode(
                x="key:O",
                y=alt.Y(
                    field="average",
                    scale=alt.Scale(type="log"),
                    type="quantitative",
                    title="average [s]",
                ),
                color=alt.Color("domain"),
            )
            .interactive()
            .properties(width=fig_width, height=fig_height)
        )
    )
    difference_meta_overall = (
        alt.Chart(df, title="Time per metadatum")
        .mark_circle(size=60)
        .encode(
            x="x:Q",
            y=alt.Y(
                field="time_difference",
                type="quantitative",
                title="difference [s]",
            ),
            color=alt.Color("domain"),
        )
        .interactive()
        .properties(width=fig_width, height=fig_height)
    )

    (
        chart1 & chart3
        | chart2 & performance_monitor
        | difference_meta_overall
    ).show()


if __name__ == "__main__":
    wants_details = True
    evaluator(wants_details)
