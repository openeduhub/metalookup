from typing import List

from psycopg2._psycopg import AsIs
from psycopg2.extensions import register_adapter
from pydantic import BaseModel, Field

from app.models import Input, Output
from lib.constants import ActionEnum


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
