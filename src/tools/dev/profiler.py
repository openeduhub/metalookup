import json
from sqlite3 import OperationalError

import requests
from sqlalchemy.orm import sessionmaker, declarative_base

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
    url = "http://extractor:5057/records"

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    print(type(response.text), len(response.text))
    records = json.loads(response.text)["out"]
    print(len(records))

    db = ProfilerSession()
    for record in records:
        print(record["id"])
        # write into local database
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


if __name__ == '__main__':
    create_metadata(profiling_engine)
    download_remote_records()
