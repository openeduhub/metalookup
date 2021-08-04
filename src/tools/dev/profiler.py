import json
import math
import sys

import requests
from sqlalchemy import inspect
from sqlalchemy.orm import Session, sessionmaker

import db.models as db_models
from db.base import create_database_engine, create_metadata
from features.website_manager import WebsiteManager
from lib.constants import ACCESSIBILITY, VALUES
from lib.settings import PROFILING_HOST_NAME
from lib.tools import get_mean, get_std_dev


def get_profiler_db():
    try:
        db = ProfilerSession()
        yield db
    finally:
        db.close()


profiling_engine = create_database_engine(
    PROFILING_HOST_NAME, "postgres", "postgres"
)
ProfilerSession = sessionmaker(
    autocommit=False, autoflush=False, bind=profiling_engine
)


def download_remote_records():
    url = "https://metalookup.openeduhub.net/records"
    # url = "http://extractor:5057/records"

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    try:
        records = json.loads(response.text)["out"]
    except TypeError as err:
        print(
            f"Exception when loading records with {err.args}.\nPotentially due to outdated record schema. "
        )
        sys.exit(1)
    print("Number of records loaded: ", len(records))

    session = ProfilerSession()
    for record in records:
        if PROFILER_DEBUG:
            print("Writing record #", record["id"])

        db_record = db_models.Record(
            timestamp=record["timestamp"],
            action=record["action"],
            url=record["url"],
            start_time=record["start_time"],
            debug=record["debug"],
            html=record["html"],
            headers=record["headers"],
            har=record["har"],
            allow_list=record["allow_list"],
            meta=record["meta"],
            exception=record["exception"],
            time_until_complete=record["time_until_complete"],
        )
        session.add(db_record)

    try:
        session.commit()
        session.close()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def print_schemas():
    inspector = inspect(profiling_engine)
    schemas = inspector.get_schema_names()

    for schema in schemas:
        print("schema: %s" % schema)
        for table_name in inspector.get_table_names(schema=schema):
            print("table_name: %s" % table_name)
            for column in inspector.get_columns(table_name, schema=schema):
                print("Column: %s" % column)


def get_total_time():
    database: Session = ProfilerSession()

    time_until_complete = database.execute(
        'SELECT time_until_complete FROM "Record"'
    )

    total_time = 0
    for time_value in time_until_complete:
        total_time += time_value[0]
    print("total_time: ", total_time)


def convert_meta_string_to_dict(meta: str) -> dict:
    if meta != "":
        meta = json.loads(meta)
        if meta is None:
            meta = {}
    else:
        meta = {}
    return meta


def parse_meta():
    database: Session = ProfilerSession()

    meta_rows = database.execute('SELECT meta FROM "Record"')

    time_per_feature = {}

    for meta_row in meta_rows:
        meta = convert_meta_string_to_dict(meta_row[0])

        for key, value in meta.items():
            if key not in time_per_feature.keys():
                time_per_feature.update({key: []})
            if value is not None:
                time_per_feature[key].append(
                    float(value["time_for_completion"])
                )

    for key, value in time_per_feature.items():
        print(f"total time per feature {key}: {sum(value)}")


def print_accessibility_per_domain():
    database: Session = ProfilerSession()

    query = database.query(db_models.Record.url, db_models.Record.meta)

    website_manager = WebsiteManager.get_instance()

    meta_rows = database.execute(query)

    print_data = {}
    for meta_row in meta_rows:
        url = meta_row[0]
        if url == "":
            continue

        website_manager.website_data.url = url
        website_manager._extract_top_level_domain()
        top_level_domain = website_manager.website_data.top_level_domain
        if top_level_domain == "":
            print("Top level domain not found for", url)

        if top_level_domain not in print_data.keys():
            print_data.update({top_level_domain: []})
        meta = convert_meta_string_to_dict(meta_row[1])
        if ACCESSIBILITY in meta.keys() and meta[ACCESSIBILITY] is not None:
            values = meta[ACCESSIBILITY][VALUES]

            for value in values:
                if value != -1:
                    print_data[top_level_domain].append(value)

    print("print_data:", print_data)
    for domain in print_data.keys():
        if domain != "" and len(print_data) > 0:
            print(
                domain,
                get_mean(print_data[domain]),
                get_std_dev(print_data[domain]),
            )


PROFILER_DEBUG = False

if __name__ == "__main__":
    create_metadata(profiling_engine)
    download_remote_records()

    if PROFILER_DEBUG:
        print_schemas()

    get_total_time()

    parse_meta()

    print_accessibility_per_domain()
