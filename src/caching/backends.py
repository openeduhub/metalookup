# from: https://github.com/long2ice/fastapi-cache
# Unfortunately, this library does not support caching of post requests (yet),
# hence we use a slightly modified own version.
import abc
import logging
import time
from asyncio import Lock
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

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
        pass


@dataclass
class Value:
    data: str
    ttl_ts: int


class InMemoryBackend(Backend):
    _store: Dict[str, Value] = {}
    _lock = Lock()

    @property
    def _now(self) -> int:
        return int(time.time())

    def _get(self, key: str):
        v = self._store.get(key)
        if v:
            if v.ttl_ts < self._now:
                del self._store[key]
            else:
                return v

    async def setup(self):
        pass  # nothing to do...

    async def get_with_ttl(self, key: str) -> Tuple[int, Optional[str]]:
        logger.info(f"get_with_ttl: {key}")
        async with self._lock:
            v = self._get(key)
            if v:
                return v.ttl_ts - self._now, v.data
            return 0, None

    async def get(self, key: str) -> Optional[str]:
        logger.info(f"get {key}")
        async with self._lock:
            v = self._get(key)
            if v:
                return v.data

    async def set(self, key: str, value: str, expire: int = None):
        logger.info(f"set {key} {value} {expire}")
        async with self._lock:
            self._store[key] = Value(value, self._now + (expire or 0))

    async def clear(self, namespace: str = None, key: str = None):
        logger.info(f"clear {key}")
        if namespace:
            keys = list(self._store.keys())
            for key in keys:
                if key.startswith(namespace):
                    del self._store[key]
        elif key:
            del self._store[key]


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
        r = await self.database.fetch_one(query="SELECT * FROM metadata_cache WHERE key = :key", values={"key": key})
        value, ttl = r["value"], r["ttl"]
        return ttl - self.now(), value

    async def get(self, key: str) -> Optional[str]:
        r = await self.database.fetch_one(query="SELECT * FROM metadata_cache WHERE key = :key", values={"key": key})
        return r if r is None else r["value"]

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
        await self.database.execute(
            query="DELETE FROM metadata_cache WHERE key = :key",
            values={"key": key},
        )
