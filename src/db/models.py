from sqlalchemy import Boolean, Column, Float, Integer, UnicodeText

from db.base import Base


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
