"""
Health check endpoint.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str = "ok"
    message: str = "Document Chat Hub API is running."
    version: str = "2.0.0"


@router.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Check if the API is running."""
    return HealthResponse()
