"""FastAPI application entrypoint."""
import logging
from pathlib import Path

from contextlib import asynccontextmanager
from sqlalchemy import text
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import api_router
from app.core.config import settings
from app.db.session import engine, init_db

logger = logging.getLogger(__name__)


def _redact_url(url: str) -> str:
    """Redact password in URL for logging."""
    if not url or "@" not in url:
        return url
    try:
        pre, rest = url.split("@", 1)
        if "://" in pre:
            scheme, rest2 = pre.split("://", 1)
            if ":" in rest2:
                user, _ = rest2.split(":", 1)
                return f"{scheme}://{user}:****@{rest}"
    except Exception:
        pass
    return "***"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Database: %s", _redact_url(settings.DATABASE_URL))
    await init_db()
    yield


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan,
)
app.include_router(api_router, prefix="/api")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return JSON for all unhandled errors; include detail when DEBUG=1."""
    logger.exception("Unhandled exception: %s", exc)
    content: dict = {"detail": "Internal server error"}
    if settings.DEBUG:
        content["debug"] = str(exc)
    return JSONResponse(status_code=500, content=content)

# Frontend: serve static files and app root
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    async def frontend() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")
else:
    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "API only. Docs: /docs", "health": "/health"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
async def health_db() -> JSONResponse:
    """Check DB connectivity; returns 200 and db status or 503 with error message."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return JSONResponse(
            status_code=200,
            content={"status": "ok", "db": "connected"},
        )
    except Exception as e:  # noqa: BLE001
        logger.exception("Health DB check failed: %s", e)
        return JSONResponse(
            status_code=503,
            content={"status": "error", "db": "disconnected", "detail": str(e)},
        )


if __name__ == "__main__":
    import uvicorn
    # No reload: avoids Windows reloader permission errors; use run_local.ps1 or uvicorn CLI
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8080,
        reload=False,
    )
