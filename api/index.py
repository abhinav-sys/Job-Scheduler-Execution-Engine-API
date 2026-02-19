"""Vercel serverless function: FastAPI app (api/ is the standard Vercel location)."""
from app.main import app

__all__ = ["app"]
