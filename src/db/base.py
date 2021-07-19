from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base

from lib.settings import STORAGE_HOST_NAME


def create_database_engine(host_name, user_name, user_password):
    database_name = "storage"
    sql_url = (
        f"postgresql://{user_name}:{user_password}@{host_name}/{database_name}"
    )
    return create_engine(sql_url)


database_engine = create_database_engine(STORAGE_HOST_NAME, "postgres", "postgres")

Base = declarative_base()


def create_metadata():
    print("Creating metadata")
    try:
        Base.metadata.create_all(bind=database_engine)
    except OperationalError as err:
        print(f"Exception with database: {err.args}")
