"""Vercel entrypoint: FastAPI app (Vercel looks for app in index.py or app/index.py)."""
from app.main import app

__all__ = ["app"]
