# from: https://github.com/long2ice/fastapi-cache
# Unfortunately, this library does not support caching of post requests (yet),
# hence we use a slightly modified own version.
import abc
import time
from asyncio import Lock
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from lib.logger import create_logger

logger = create_logger()


class Backend:
    @abc.abstractmethod
    async def get_with_ttl(self, key: str) -> tuple[int, Optional[str]]:
        """If not found, return None for the value. the returned ttl may be anything."""

    @abc.abstractmethod
    async def get(self, key: str) -> str:
        pass

    @abc.abstractmethod
    async def set(self, key: str, value: str, expire: int = None):
        pass

    @abc.abstractmethod
    async def clear(self, key: str = None) -> int:
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

    async def get_with_ttl(self, key: str) -> Tuple[int, Optional[str]]:
        logger.info(f"get_with_ttl: {key}")
        async with self._lock:
            v = self._get(key)
            if v:
                return v.ttl_ts - self._now, v.data
            return 0, None

    async def get(self, key: str) -> str:
        logger.info(f"get {key}")
        async with self._lock:
            v = self._get(key)
            if v:
                return v.data

    async def set(self, key: str, value: str, expire: int = None):
        logger.info(f"set {key} {value} {expire}")
        async with self._lock:
            self._store[key] = Value(value, self._now + (expire or 0))

    async def clear(self, namespace: str = None, key: str = None) -> int:
        logger.info(f"clear {key}")
        count = 0
        if namespace:
            keys = list(self._store.keys())
            for key in keys:
                if key.startswith(namespace):
                    del self._store[key]
                    count += 1
        elif key:
            del self._store[key]
            count += 1
        return count
