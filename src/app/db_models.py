from typing import List

from psycopg2._psycopg import AsIs
from psycopg2.extensions import register_adapter
from pydantic import Field, BaseModel
from sqlalchemy import Boolean, Column, Float, Integer, UnicodeText

from app.models import Input, Output
from db.base import Base
from lib.constants import ActionEnum


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


def adapt_action_enum(action):
    return AsIs(repr(action.value))


register_adapter(ActionEnum, adapt_action_enum)


class RecordSchema(Output, Input):
    id: int = Field(default=-1, description="Primary key")
    timestamp: float = Field(
        default=-1, description="timestamp in milliseconds"
    )
    start_time: float = Field(
        default=-1, description="timestamp of start in milliseconds"
    )
    action: ActionEnum = Field(
        default=ActionEnum.NONE, description="Either 'response' or 'request'"
    )
    allow_list: str = Field(
        default="",
        description="Overwrite of original allow_list. Storing as json string",
    )
    meta: str = Field(
        default="",
        description="Overwrite of original meta. Storing as json string",
    )


class RecordsOutput(BaseModel):
    records: List[RecordSchema] = Field(default="[]")

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
