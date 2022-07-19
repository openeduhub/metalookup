# from: https://github.com/long2ice/fastapi-cache
# Unfortunately, this library does not support caching of post requests (yet),
# hence we use a slightly modified own version.
import abc
import logging
import time
from typing import Optional

from databases import Database

logger = logging.getLogger(__name__)


class Backend:
    @abc.abstractmethod
    async def setup(self):
        """Run intialization routines for the backend at application startup."""

    @abc.abstractmethod
    async def get_with_ttl(self, key: str) -> tuple[int, Optional[str]]:
        """If not found, return None for the value. the returned ttl may be anything."""

    @abc.abstractmethod
    async def get(self, key: str) -> Optional[str]:
        pass

    @abc.abstractmethod
    async def set(self, key: str, value: str, expire: int = None):
        pass

    @abc.abstractmethod
    async def clear(self, key: str = None):
        """If no key is provided, truncate the whole cache, otherwise remove only the entry with given key."""
        pass


class DatabaseBackend(Backend):
    """Implement caching backend for any database supported by the databases python package."""

    def __init__(self, url: str):
        self.database = Database(url)
        if self.database.url.dialect not in ("sqlite", "postgresql"):
            raise ValueError(f"Unsupported dialect: {self.database.url.dialect}. Supported: sqlite, postgresql")

    @staticmethod
    def now() -> int:
        return int(time.time())

    async def setup(self):
        await self.database.connect()
        query = """
        CREATE TABLE IF NOT EXISTS metadata_cache (
                key VARCHAR PRIMARY KEY,
                ttl INTEGER,
                value VARCHAR
        )
        """
        await self.database.execute(query=query)

    async def get_with_ttl(self, key: str) -> tuple[int, Optional[str]]:
        result = await self.database.fetch_one(
            query="SELECT * FROM metadata_cache WHERE key = :key", values={"key": key}
        )
        if result is None:
            return -1, None
        value, ttl = result["value"], result["ttl"]
        return ttl - self.now(), value

    async def get(self, key: str) -> Optional[str]:
        result = await self.database.fetch_one(
            query="SELECT * FROM metadata_cache WHERE key = :key", values={"key": key}
        )
        return result if result is None else result["value"]

    async def set(self, key: str, value: str, expire: int = None):
        # upsert data, works for postgres and sqlite databases.
        await self.database.execute(
            query="""
            INSERT INTO metadata_cache (key, ttl, value) VALUES (:key, :ttl, :value)
             ON CONFLICT (key) DO UPDATE SET ttl = EXCLUDED.ttl, value=EXCLUDED.value
             """,
            values={"key": key, "ttl": self.now() + (expire or 0), "value": value},
        )

    async def clear(self, key: str = None):
        if key is None:
            await self.database.execute(query="DELETE FROM metadata_cache;")
        else:
            await self.database.execute(
                query="DELETE FROM metadata_cache WHERE key = :key",
                values={"key": key},
            )
