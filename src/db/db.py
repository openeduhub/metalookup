from sqlalchemy import create_engine

# Dependency
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from lib.settings import USED_IN_PRODUCTION


def get_db():
    try:
        db = SessionLocal()
        print(f"getting db {db}")
        yield db
    finally:
        print("closing db")
        db.close()


def create_server_connection(host_name, user_name, user_password):
    database_name = "storage"
    sql_url = f'postgresql://{user_name}:{user_password}@{host_name}/{database_name}'
    connection = create_engine(sql_url)
    print("connection: ", connection)
    return connection


# TODO: use debug flag or similar
if USED_IN_PRODUCTION:
    engine = create_server_connection("db", "postgres", "postgres")
else:
    engine = create_server_connection("localhost", "postgres", "postgres")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
