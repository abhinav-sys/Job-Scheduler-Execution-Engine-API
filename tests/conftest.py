"""Pytest fixtures."""
import pytest
from httpx import ASGITransport, AsyncClient

# Ensure .env is loaded so tests use same config as app (or CI env vars)
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Async HTTP client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
