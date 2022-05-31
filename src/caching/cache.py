# from: https://github.com/long2ice/fastapi-cache
# Unfortunately, this library does not support caching of post requests (yet),
# hence we use a slightly modified own version.
import asyncio
import json
import logging
from functools import wraps
from typing import Optional, Protocol

from fastapi import HTTPException, Request, Response

from caching.backends import Backend

logger = logging.getLogger(__name__)


class KeyBuilder(Protocol):
    def __call__(self, **kwargs) -> Optional[str]:
        """Should return none if the request is not suitable for caching."""


def cache(expire: int, key: KeyBuilder, backend: Optional[Backend]):
    """
    Eventually cache the response of a request and handle future incoming requests by simply loading the
    response from cache.
    :param expire: How long (seconds) a stored cache entry will be valid.
    :param backend: The cache storage engine to be used. If None, then no caching will be performed and the decorator
                    will have no effect.
    :param key: A function that defines whether an incoming request can be cached and under which key it will be cached.
                It will take the same arguments as the decorated function and should return a string key if the request
                can be cached, or None otherwise.
    :return: A function that just looks like the decorated function but is wrapped with caching behaviour.
    """

    def wrapper(func):
        # Note:
        # functools.wraps essentially makes the wrapper function looking exactly like the wrapped function.
        # This means, that registering the wrapper function with a fastapi router will look to fastapi like
        # registering the original function. Hence we cannot add the 'request: Request, response: Response'
        # arguments to the wrapper (they would not be provided by fastapi, because fastapi only sees the wrapped
        # signature).
        # On the other hand, we cannot not use wraps, as the cache decorator should work for arbitrary signatures
        # which requires variadic args and kwargs.
        # While it might be possible to do some magical signature transformations to work around this issue,
        # it is far easier to simply force usage of the request and response arguments in the wrapped function.
        if backend is None:
            logger.info(f"No cache backend provided. Caching disabled for {func}")
            return func

        @wraps(func)
        async def inner(
            *args,
            **kwargs,
        ):
            assert (
                "request" in kwargs and "response" in kwargs
            ), "Cache decorator needs request and response arguments to work"

            request: Request = kwargs["request"]
            response: Response = kwargs["response"]

            no_cache = "no-cache" in request.headers.get("Cache-Control", "")
            only_if_cached = "only-if-cached" in request.headers.get("Cache-Control", "")

            unsupported_method = request.method not in {"GET", "POST"}
            if no_cache or unsupported_method:
                logger.info(f"Caching disabled by Cache-Control: {request.headers.get('Cache-Control')}")
                return await func(*args, **kwargs)

            cache_key = key(**kwargs)

            if cache_key is None and only_if_cached:
                logger.debug("Request cannot be served from cache")
                # todo: discuss: This is somewhat questionable. If the user requests a response served
                #       from cache, but the response is not cached - and can never be, what should we do?
                raise HTTPException(status_code=400, detail="Request never be served from cache.")
            elif cache_key is None:
                logger.debug("Caching not supported for request")
                return await func(*args, **kwargs)

            age, ret = await backend.get_with_ttl(cache_key)

            if ret is None and only_if_cached:
                logger.debug("Request cannot be served from cache")
                # todo: discuss: This is somewhat questionable. If the user requests a response served
                #       from cache, but the response is not cached, what should we do? Other servers use 50x
                #       response codes to indicate that no such answer can be delivered from the cache.
                raise HTTPException(status_code=404, detail="Request cannot be served from cache.")

            if ret is None:
                logger.debug("Request cannot be served from cache. Evaluating function and populating cache")
                ret = await func(*args, **kwargs)
                response.headers.append("Age", "0")
                logger.debug("Populating cache")
                # store the result in cache, no need to wait for
                # it to complete before we send out the response
                if "no-store" not in response.headers.getlist("Cache-Control"):
                    asyncio.create_task(backend.set(cache_key, ret.json(), expire))
                return ret
            else:
                response.headers.append("Age", str(age))

                return json.loads(ret)

        return inner

    return wrapper
