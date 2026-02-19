"""Vercel serverless entrypoint: expose FastAPI app for zero-config deploy."""
from app.main import app

__all__ = ["app"]
