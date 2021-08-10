from unittest import mock

import pytest
import sqlalchemy.exc

from app.schemas import RecordSchema
from db.db import create_dummy_record, load_cache


@pytest.fixture
def session():
    with mock.patch("sqlalchemy.orm.sessionmaker") as sessionmaker:
        session = sessionmaker()

    return session


"""
--------------------------------------------------------------------------------
"""


def test_create_dummy_record():
    output = create_dummy_record()

    assert isinstance(output, RecordSchema)
    assert output.id == -1
    assert output.url == ""
    assert output.html == ""
    assert output.headers == ""
    assert output.har == ""
    assert output.allow_list == ""
    assert output.meta == ""
    assert output.exception == ""


"""
--------------------------------------------------------------------------------
"""


def test_load_cache():
    empty_cache = []

    with mock.patch("db.db.SessionLocal") as session_local:
        session_local().__enter__().query().all.return_value = empty_cache
        output = load_cache()
        empty_cache_loaded = output == empty_cache

    assert empty_cache_loaded

    with mock.patch("db.db.SessionLocal") as session_local:
        session_local().__enter__().query().all.side_effect = sqlalchemy.exc.SQLAlchemyError
        output = load_cache()
        empty_cache_loaded = output == empty_cache

    assert empty_cache_loaded

