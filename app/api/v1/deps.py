"""
Shared FastAPI dependencies.
"""

from fastapi import Depends

from app.core.security import require_api_key


async def get_api_key(key: str = Depends(require_api_key)) -> str:
    """Dependency that provides a validated API key."""
    return key
