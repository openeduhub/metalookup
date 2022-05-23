import json

import sqlalchemy.exc
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import sessionmaker

import db.models as db_models
from db.base import database_engine
from lib.logger import get_logger

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=database_engine)


def load_cache():
    with SessionLocal() as session:
        try:
            cache = session.query(db_models.CacheEntry).all()
        except sqlalchemy.exc.SQLAlchemyError as err:
            session.rollback()
            print(f"Error while loading cache: {err.args}")
            cache = []
    return cache


def get_top_level_domains():
    with SessionLocal() as session:
        try:
            entries = session.query(db_models.CacheEntry.top_level_domain).all()
        except sqlalchemy.exc.SQLAlchemyError as err:
            session.rollback()
            entries = []
            print(f"Error while loading top level domains: {err.args}, {str(err)}")
    return [entry[0] for entry in entries]


def create_cache_entry(top_level_domain: str, feature: str, values: dict, logger):
    logger.debug("Writing to cache")

    with SessionLocal() as session:
        try:
            entry = session.query(db_models.CacheEntry).filter_by(top_level_domain=top_level_domain).first()

            if entry is None:
                entry = db_models.CacheEntry(
                    **{
                        "top_level_domain": top_level_domain,
                        feature: [json.dumps(values)],
                    }
                )
                session.add(entry)
            else:
                updated_values = entry.__getattribute__(feature)
                updated_values.append(json.dumps(values))
                session.query(db_models.CacheEntry).filter_by(top_level_domain=top_level_domain).update(
                    {feature: updated_values}
                )

            session.commit()
        except (sqlalchemy.exc.SQLAlchemyError, TypeError) as err:
            print(f"err: {str(err)} {err.args}")
            session.rollback()
            logger.error(f"Writing failed with {err.args}, {str(err)}")
            raise


def reset_cache(domain: str) -> int:
    logger = get_logger()
    logger.info(f"Resetting cache for domain: {'all' if domain == '' else domain}")

    session = SessionLocal()
    try:
        if domain == "":
            resulting_row_count: int = session.query(db_models.CacheEntry).delete()
        else:
            resulting_row_count: int = session.query(db_models.CacheEntry).filter_by(top_level_domain=domain).delete()
        session.commit()
        session.close()
    except sqlalchemy.exc.SQLAlchemyError as err:
        session.rollback()
        logger.error(f"Resetting cache failed with {err.args}, {str(err)}")
        raise
    finally:
        session.close()

    return resulting_row_count


def read_cached_values_by_feature(key: str, domain: str) -> list:
    logger = get_logger()
    with SessionLocal() as session:
        try:
            entry = session.query(db_models.CacheEntry).filter_by(top_level_domain=domain).first()
        except (ProgrammingError, AttributeError) as e:
            logger.exception(f"Reading cache failed: {e.args}")
            entry = []
        if entry is None:
            return []
    return entry.__getattribute__(key)
