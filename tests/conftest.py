"""Shared fixtures.

`app` is imported from ``main`` after Plan 05 defines the FastAPI instance.
"""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from main import app


@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
