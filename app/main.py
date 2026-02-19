"""FastAPI application entrypoint."""
import logging
from pathlib import Path

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import api_router
from app.core.config import settings
from app.db.session import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    """Return JSON for all unhandled errors so the frontend never gets plain-text 500."""
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

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


if __name__ == "__main__":
    import uvicorn
    # No reload: avoids Windows reloader permission errors; use run_local.ps1 or uvicorn CLI
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8080,
        reload=False,
    )
