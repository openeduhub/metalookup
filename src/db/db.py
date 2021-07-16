import json

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import sessionmaker

from app import db_models
from app.db_models import RecordSchema
from app.models import Input, Output
from db.base import engine
from lib.constants import ActionEnum


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_request_record(
        timestamp: float, input_data: Input, allowance: dict
):
    print("Writing request to db")
    db = SessionLocal()
    new_input = db_models.Record(
        timestamp=timestamp,
        action=ActionEnum.REQUEST,
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


def create_response_record(
        timestamp: float,
        end_time: float,
        input_data: Input,
        allowance: dict,
        output: Output,
):
    print("Writing response to db")
    json_compatible_meta = jsonable_encoder(output.meta)
    db = SessionLocal()
    new_input = db_models.Record(
        timestamp=end_time,
        action=ActionEnum.RESPONSE,
        url=input_data.url,
        start_time=timestamp,
        debug=input_data.debug,
        html=input_data.html,
        headers=input_data.headers,
        har=input_data.har,
        allow_list=json.dumps(allowance),
        meta=json.dumps(json_compatible_meta),
        exception=output.exception,
        time_until_complete=output.time_until_complete,
    )

    db.add(new_input)
    db.commit()
    db.close()


def create_dummy_record() -> RecordSchema:
    record = RecordSchema(
        id=-1,
        timestamp=-1,
        start_time=-1,
        action=ActionEnum.NONE,
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
