from unittest import mock

import pytest
import sqlalchemy.exc

from app.schemas import RecordSchema
from db.db import (
    create_cache_entry,
    create_dummy_record,
    get_top_level_domains,
    load_cache,
)
from db.models import CacheEntry


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
        session_local().__enter__().query().all.side_effect = (
            sqlalchemy.exc.SQLAlchemyError("Unit test")
        )
        output = load_cache()
        empty_cache_loaded = output == empty_cache

    assert empty_cache_loaded

    entry = CacheEntry()

    entry.top_level_domain = "test_domain"
    example_cache_entry = [entry]
    with mock.patch("db.db.SessionLocal") as session_local:
        session_local().__enter__().query().all.return_value = (
            example_cache_entry
        )
        output = load_cache()
        cache_loaded = output == example_cache_entry
        correct_domain = output[0].top_level_domain == entry.top_level_domain

    assert cache_loaded and correct_domain


"""
--------------------------------------------------------------------------------
"""


def test_get_top_level_domains():
    empty_cache = []

    with mock.patch("db.db.SessionLocal") as session_local:
        session_local().__enter__().query().all.return_value = empty_cache
        output = get_top_level_domains()
        empty_cache_loaded = output == empty_cache

    assert empty_cache_loaded

    with mock.patch("db.db.SessionLocal") as session_local:
        session_local().__enter__().query().all.side_effect = (
            sqlalchemy.exc.SQLAlchemyError("Unit test")
        )
        output = get_top_level_domains()
        empty_cache_loaded = output == empty_cache

    assert empty_cache_loaded

    test_domain = "test_domain"
    example_cache_entry = [(test_domain, "random_other_entry_information")]
    with mock.patch("db.db.SessionLocal") as session_local:
        session_local().__enter__().query().all.return_value = (
            example_cache_entry
        )
        output = get_top_level_domains()
        cache_loaded = output == [test_domain]
        correct_domain = output[0] == test_domain

    assert cache_loaded and correct_domain


"""
--------------------------------------------------------------------------------
"""


def test_create_cache_entry(mocker):
    empty_cache = []

    domain = "br"
    feature = "test"
    values = {}
    logger = mocker.MagicMock()

    with mock.patch("db.db.SessionLocal") as session_local:
        entry = mocker.MagicMock()
        entry.return_value = {feature: empty_cache}
        session_local().__enter__().query().filter_by().first.return_value = (
            entry
        )
        session_local().__enter__().query().filter_by().first().__getattribute__ = (
            mocker.MagicMock()
        )
        session_local().__enter__().query().filter_by().first().__getattribute__.return_value = (
            empty_cache
        )
        create_cache_entry(domain, feature, values, logger)

        assert session_local.call_count == 4

    with mock.patch("db.db.SessionLocal") as session_local:
        session_local().__enter__().query().filter_by().first.return_value = (
            None
        )
        with pytest.raises(TypeError):
            create_cache_entry(domain, feature, values, logger)

        assert session_local.call_count == 2

    with mock.patch("db.db.SessionLocal") as session_local:
        session_local().__enter__().query().filter_by().first.return_value = (
            None
        )
        create_cache_entry(domain, "advertisement", values, logger)

        assert session_local.call_count == 2

    with mock.patch("db.db.SessionLocal") as session_local:
        session_local.side_effect = sqlalchemy.exc.SQLAlchemyError("Unit test")
        with pytest.raises(sqlalchemy.exc.SQLAlchemyError):
            create_cache_entry(domain, feature, values, logger)

        assert session_local.call_count == 1
