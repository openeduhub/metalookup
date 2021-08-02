from sqlalchemy import Boolean, Column, Float, Integer, UnicodeText
from sqlalchemy.dialects.postgresql import ARRAY

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
    allow_list = Column(UnicodeText)
    meta = Column(UnicodeText)
    exception = Column(UnicodeText)
    time_until_complete = Column(Float)


class CacheEntry(Base):
    __tablename__ = "CacheEntry"
    top_level_domain = Column(UnicodeText, primary_key=True)
    advertisement = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    easy_privacy = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    malicious_extensions = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    extracted_links = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    extract_from_files = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    cookies_in_html = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    cookies = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    fanboy_annoyance = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    fanboy_notification = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    fanboy_social_media = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    anti_adblock = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    easylist_germany = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    easylist_adult = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    paywall = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    security = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    iframe_embeddable = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    pop_up = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    reg_wall = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    log_in_out = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    accessibility = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    g_d_p_r = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    javascript = Column(ARRAY(UnicodeText, dimensions=1), default=[])
    metatag_explorer = Column(ARRAY(UnicodeText, dimensions=1), default=[])
