from pydantic import Field

from sqlalchemy import Column, Integer, Text, Float, Boolean, JSON, UnicodeText

from app.models import Output, Input
from db.db import Base


class Record(Base):
    __tablename__ = "Record"
    timestamp = Column(Integer, primary_key=True, index=True)
    action = Column(UnicodeText)
    url = Column(UnicodeText)
    html = Column(UnicodeText)
    headers = Column(UnicodeText)
    har = Column(UnicodeText)
    debug = Column(Boolean)
    allow_list = Column(JSON)  # dump json for now
    meta = Column(JSON)  # dump json for now
    exception = Column(UnicodeText)
    time_until_complete = Column(Float)


class RecordSchema(Output, Input):
    timestamp: int = Field(default=-1, description="timestamp in milliseconds")

    class Config:
        orm_mode = True
