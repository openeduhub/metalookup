import json

from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session, sessionmaker

import db.models as db_models
from app.models import Input, Output
from app.schemas import RecordSchema
from db.base import database_engine
from lib.constants import ActionEnum
from lib.logger import create_logger


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=database_engine
)


def create_request_record(
    timestamp: float, input_data: Input, allowance: dict
):
    print("Writing request to db")
    session = SessionLocal()
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

    session.add(new_input)
    session.commit()
    session.close()


def create_response_record(
    timestamp: float,
    end_time: float,
    input_data: Input,
    allowance: dict,
    output: Output,
):
    print("Writing response to db")
    json_compatible_meta = jsonable_encoder(output.meta)
    session = SessionLocal()
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

    session.add(new_input)
    session.commit()
    session.close()


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
        debug=False,
        allow_list="",
        meta="",
        exception="",
        time_until_complete=-1,
    )
    return record


def load_records(session: Session = SessionLocal()) -> [db_models.Record]:
    try:
        records = session.query(db_models.Record).all()
    except (OperationalError, ProgrammingError) as err:
        dummy_record = create_dummy_record()
        dummy_record.exception = f"Database exception: {err.args}"
        records = [dummy_record]
    return records


def load_cache(session: Session = SessionLocal()):
    try:
        cache = session.query(db_models.CacheEntry).all()
    except (OperationalError, ProgrammingError) as err:
        print("Error while loading cache:", err.args)
        cache = []
    return cache


def get_top_level_domains():
    session = SessionLocal()
    entries = session.query(db_models.CacheEntry.top_level_domain).all()
    return [entry[0] for entry in entries]


def create_cache_entry(
    top_level_domain: str, feature: str, values: dict, logger
):
    logger.debug("Writing to cache")

    session = SessionLocal()

    try:
        entry = (
            session.query(db_models.CacheEntry)
            .filter_by(top_level_domain=top_level_domain)
            .first()
        )

        if entry is None:
            entry = db_models.CacheEntry(
                **{
                    "top_level_domain": top_level_domain,
                    feature: [json.dumps(values)],
                }
            )
            session.add(entry)
        else:
            updated_values = entry.__getattribute__(feature)
            updated_values.append(json.dumps(values))
            session.query(db_models.CacheEntry).filter_by(
                top_level_domain=top_level_domain
            ).update({feature: updated_values})

        session.commit()
    finally:
        session.close()
        logger.debug("Writing done")


def reset_cache() -> int:
    logger = create_logger()
    logger.debug("Resetting cache")

    session = SessionLocal()
    resulting_row_count: int = session.query(db_models.CacheEntry).delete()
    session.commit()
    session.close()

    return resulting_row_count
