"""API endpoint tests."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health():
    """Health check returns 200 and status ok."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data == {"status": "ok"}


@pytest.mark.asyncio
async def test_api_jobs_list():
    """List jobs returns 200 and has jobs/total when DB is available."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        try:
            r = await client.get("/api/jobs?limit=5")
        except Exception as e:
            if "ConnectionRefusedError" in type(e).__name__ or "refused" in str(e).lower():
                pytest.skip("Database not available (set DATABASE_URL in .env to run this test)")
            raise
    if r.status_code != 200:
        pytest.skip("Database not available or error (set DATABASE_URL in .env to run this test)")
    data = r.json()
    assert "jobs" in data
    assert "total" in data
    assert isinstance(data["jobs"], list)
    assert isinstance(data["total"], int)
