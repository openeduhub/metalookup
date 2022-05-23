from typing import List

from psycopg2._psycopg import AsIs
from psycopg2.extensions import register_adapter
from pydantic import BaseModel, Field

from lib.constants import ActionEnum


def adapt_action_enum(action):
    return AsIs(repr(action.value))


register_adapter(ActionEnum, adapt_action_enum)


class CacheSchema(BaseModel):
    top_level_domain: str = Field(default="", description="Primary key")
    advertisement: List[str] = Field(default=[])
    easy_privacy: List[str] = Field(default=[])
    malicious_extensions: List[str] = Field(default=[])
    extracted_links: List[str] = Field(default=[])
    extract_from_files: List[str] = Field(default=[])
    cookies: List[str] = Field(default=[])
    fanboy_annoyance: List[str] = Field(default=[])
    fanboy_notification: List[str] = Field(default=[])
    fanboy_social_media: List[str] = Field(default=[])
    anti_adblock: List[str] = Field(default=[])
    easylist_germany: List[str] = Field(default=[])
    easylist_adult: List[str] = Field(default=[])
    paywall: List[str] = Field(default=[])
    security: List[str] = Field(default=[])
    iframe_embeddable: List[str] = Field(default=[])
    pop_up: List[str] = Field(default=[])
    reg_wall: List[str] = Field(default=[])
    log_in_out: List[str] = Field(default=[])
    accessibility: List[str] = Field(default=[])
    g_d_p_r: List[str] = Field(default=[])
    javascript: List[str] = Field(default=[])
    metatag_explorer: List[str] = Field(default=[])

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class CacheOutput(BaseModel):
    cache: List[CacheSchema] = Field(default=[])

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
