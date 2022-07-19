import time

import pytest

from metalookup.caching.backends import DatabaseBackend


@pytest.mark.asyncio
async def test_backend(tmpdir):
    backend = DatabaseBackend(url=f"sqlite:///{tmpdir}/test.db")
    await backend.setup()

    assert await backend.get(key="some-key") is None
    await backend.set(key="some-key", value="some-value", expire=100)
    assert await backend.get(key="some-key") == "some-value"
    expire, value = await backend.get_with_ttl(key="some-key")
    assert expire <= 100
    assert value == "some-value"
    time.sleep(1)
    expire, value = await backend.get_with_ttl(key="some-key")
    assert expire <= 99
    assert value == "some-value"


@pytest.mark.asyncio
async def test_backend_postgres():
    # uses the configuration from docker-compose.yaml db container
    backend = DatabaseBackend(url="postgresql://metalookup:metalookup@localhost/metalookup")
    try:
        await backend.setup()
    except OSError as e:
        print(e)
        pytest.skip("Failed to connect to postgres, probably container is not running. Skipping test")

    await backend.set(key="some-key", value="some-value", expire=100)
    assert await backend.get(key="some-key") == "some-value"
    expire, value = await backend.get_with_ttl(key="some-key")
    assert expire <= 100
    assert value == "some-value"

    time.sleep(1)

    expire, value = await backend.get_with_ttl(key="some-key")
    assert expire <= 99
    assert value == "some-value"
