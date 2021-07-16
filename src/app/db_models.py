from typing import Optional

from pydantic import Field
from sqlalchemy import (
    Boolean,
    Column,
    Float,
    Integer,
    UnicodeText,
    create_engine,
)
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base

from app.models import Input, Output
from lib.settings import STORAGE_HOST_NAME


def create_server_connection(host_name, user_name, user_password):
    database_name = "storage"
    sql_url = (
        f"postgresql://{user_name}:{user_password}@{host_name}/{database_name}"
    )
    return create_engine(sql_url)


engine = create_server_connection(STORAGE_HOST_NAME, "postgres", "postgres")

Base = declarative_base()

try:
    Base.metadata.create_all(bind=engine)
except OperationalError as err:
    print(f"Exception with database: {err.args}")


class Record(Base):
    __tablename__ = "Record"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(Float)
    start_time = Column(Float)
    action = Column(UnicodeText)
    url = Column(UnicodeText)
    html = Column(UnicodeText)
    headers = Column(UnicodeText)
    har = Column(UnicodeText)
    debug = Column(Boolean)
    allow_list = Column(UnicodeText)  # dump json for now
    meta = Column(UnicodeText)  # dump json for now
    exception = Column(UnicodeText)
    time_until_complete = Column(Float)


class RecordSchema(Output, Input):
    id: int = Field(default=-1, description="Primary key")
    timestamp: float = Field(
        default=-1, description="timestamp in milliseconds"
    )
    start_time: float = Field(
        default=-1, description="timestamp of start in milliseconds"
    )
    action: str = Field(
        default="", description="Either 'response' or 'request'"
    )
    allow_list: str = Field(
        default="",
        description="Overwrite of original allow_list. Storing as json string",
    )
    meta: str = Field(
        default="",
        description="Overwrite of original meta. Storing as json string",
    )

    class Config:
        orm_mode = True
