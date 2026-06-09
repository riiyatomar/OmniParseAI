"""
Aggregate all v1 endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.ingest import router as ingest_router
from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.sessions import router as sessions_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(ingest_router)
api_router.include_router(chat_router)
api_router.include_router(sessions_router)
