from fastapi import APIRouter

from app.api.routes import cron, jobs

api_router = APIRouter()
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(cron.router, prefix="/cron", tags=["cron"])
