import asyncio
import logging
from collections import deque

from aiohttp import ClientError, ClientSession
from pydantic import HttpUrl

import metalookup.lib.settings
from metalookup.app.models import Input
from metalookup.lib.tools import runtime


# Note: This function needs to be in global context to be pickleable in order to be transferable to other process.
def warmup(urls: list[HttpUrl], n_tasks: int = metalookup.lib.settings.CACHE_WARMUP_CONCURRENCY):
    """
    A function that can be passed to a subprocess which will concurrently issue requests on the extract endpoint
    for the passed list of urls.
    Note:
    This function simply is issuing concurrent requests to the actual API process - i.e. it does not do any of the
    actual work. This means, if we use 100 tasks here we do not provide the service itself with more concurrency, but
    instead only put a huge load (100 concurrent requests each needing CPU and RAM) on the service. The ability of the
    service to deal with higher loads is controlled via uvicorn and the ProcessPool size used for dispatching CPU
    heavy extractions.
    :param urls: The list of urls for which to run requests.
    :param n_tasks: How many concurrent tasks to use.
    """

    logging.basicConfig(
        level=metalookup.lib.settings.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    async def tasks(queue: deque[HttpUrl]):
        """Create and await a bunch of concurrent tasks that concurrently issue extract requests."""
        initial_queue_size = len(queue)

        async def task(id: int):
            async with ClientSession() as client:
                while not len(queue) == 0:
                    url = queue.pop()
                    logging.info(f"Task {id} [{len(queue) / initial_queue_size:2.1%}]: Warming up {url}")
                    try:
                        await client.post(
                            url=f"http://localhost:{metalookup.lib.settings.API_PORT}/extract?extra=true",
                            json=Input(url=url).dict(),
                        )
                    except ClientError:
                        logging.exception(f"Failed to warmup cache for {url}. Continuing with next in queue.")
                    # See: https://github.com/aio-libs/aiohttp/issues/5582
                    #      We also need to catch this (until above eventually gets fixed)
                    except asyncio.exceptions.TimeoutError:
                        logging.exception(f"Failed to warmup cache for {url}: Request timed out.")

        # wait until all tasks have completed meaning the queue of to-be-processed urls is empty.
        await asyncio.gather(*[task(id=id) for id in range(n_tasks)])

    logging.info(f"Starting cache warmup with {len(urls)} urls and {n_tasks} concurrent tasks.")
    with runtime() as t:
        asyncio.run(tasks(queue=deque(urls)))
    logging.info(f"Finished cache warmup with {len(urls)} urls in {t()} seconds)")
