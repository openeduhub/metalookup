import json

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import sessionmaker

from app import db_models
from app.db_models import RecordSchema, engine
from app.models import Input, Output


def get_db():
    try:
        db = SessionLocal()
        print(f"getting db {db}")
        yield db
    finally:
        print("closing db")
        db.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_request_record(
    timestamp: float, input_data: Input, allowance: dict
):
    print("Writing to db")
    db = SessionLocal()
    new_input = db_models.Record(
        timestamp=timestamp,
        action="REQUEST",
        url=input_data.url,
        start_time=-1,
        debug=input_data.debug,
        html=input_data.html,
        headers=input_data.headers,
        har=input_data.har,
        allow_list=json.dumps(allowance),
        meta="",
        exception="",
        time_until_complete=0,
    )

    db.add(new_input)
    db.commit()
    db.close()
    print("Wrote request: ", new_input)


def create_response_record(
    timestamp: float,
    end_time: float,
    input_data: Input,
    allowance: dict,
    output: Output,
):
    print("Writing to db")
    print(f"Writing to db with meta {output.meta}")

    json_compatible_item_data = jsonable_encoder(output.meta)
    print(f"Writing to db with json {json_compatible_item_data}")
    db = SessionLocal()
    new_input = db_models.Record(
        timestamp=end_time,
        action="RESPONSE",
        url=input_data.url,
        start_time=timestamp,
        debug=input_data.debug,
        html=input_data.html,
        headers=input_data.headers,
        har=input_data.har,
        allow_list=json.dumps(allowance),
        meta=json.dumps(json_compatible_item_data),
        exception=output.exception,
        time_until_complete=output.time_until_complete,
    )

    db.add(new_input)
    db.commit()
    db.close()
    print("Wrote response: ", new_input)


def create_dummy_record() -> RecordSchema:
    record = RecordSchema(
        id=-1,
        timestamp=-1,
        start_time=-1,
        action="",
        url="",
        html="",
        headers="",
        har="",
        debug="",
        allow_list="",
        meta="",
        exception="",
        time_until_complete=-1,
    )
    return record
