from typing import Optional

from pydantic import Field

from sqlalchemy import Column, Integer, Text, Float, Boolean, JSON, UnicodeText, BigInteger

from app.models import Output, Input
from db.db import Base


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
    timestamp: float = Field(default=-1, description="timestamp in milliseconds")
    start_time: float = Field(default=-1, description="timestamp of start in milliseconds")
    action: str = Field(default="", description="TBD")
    url: str = Field(default="", description="TBD")
    html: str = Field(default="", description="TBD")
    headers: str = Field(default="", description="TBD")
    har: str = Field(default="", description="TBD")
    debug: str = Field(default=False, description="TBD")
    allow_list: str = Field(default="", description="TBD")
    meta: str = Field(default="", description="TBD")
    exception: Optional[str] = Field(default="", description="TBD")
    time_until_complete: float = Field(default=-1, description="TBD")

    class Config:
        orm_mode = True
