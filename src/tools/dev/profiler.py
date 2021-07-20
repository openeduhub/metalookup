import json
import sys

import requests
from sqlalchemy import inspect
from sqlalchemy.orm import Session, sessionmaker

from app import db_models
from db.base import create_database_engine, create_metadata
from lib.settings import PROFILING_HOST_NAME


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

    db = ProfilerSession()
    for record in records:
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
        db.add(db_record)

    db.commit()
    db.close()


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


def parse_meta():
    database: Session = ProfilerSession()

    meta_rows = database.execute('SELECT meta FROM "Record"')

    time_per_feature = {}

    for meta_row in meta_rows:
        if meta_row[0] != "":
            meta = json.loads(meta_row[0])
        else:
            meta = {}

        for key, value in meta.items():
            if key not in time_per_feature.keys():
                time_per_feature.update({key: []})
            time_per_feature[key].append(float(value["time_for_completion"]))

    for key, value in time_per_feature.items():
        print(f"total time per feature {key}: {sum(value)}")


if __name__ == "__main__":
    create_metadata(profiling_engine)
    download_remote_records()

    print_schemas()

    get_total_time()

    parse_meta()
