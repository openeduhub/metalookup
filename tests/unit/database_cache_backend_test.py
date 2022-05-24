import time

import pytest

from caching.backends import DatabaseBackend


@pytest.mark.asyncio
async def test_backend(tmpdir):
    backend = DatabaseBackend(url=f"sqlite:///{tmpdir}/test.db")
    await backend.setup()

    assert await backend.get("foo") is None
    await backend.set("foo", "bar", 100)
    assert await backend.get("foo") == "bar"
    assert await backend.get_with_ttl("foo") == (100, "bar")
    time.sleep(3)
    assert await backend.get_with_ttl("foo") == (97, "bar")


@pytest.mark.asyncio
async def test_backend_postgres():
    # uses the configuration from docker-compose.yaml db container
    backend = DatabaseBackend(url="postgresql://postgres:postgres@localhost/storage")
    try:
        await backend.setup()
    except OSError as e:
        print(e)
        pytest.skip("Failed to connect to postgres, probably container is not running. Skipping test")

    await backend.set("foo", "bar", 100)
    assert await backend.get("foo") == "bar"
    assert await backend.get_with_ttl("foo") == (100, "bar")
    time.sleep(3)
    assert await backend.get_with_ttl("foo") == (97, "bar")
