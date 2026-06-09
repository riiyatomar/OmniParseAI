"""
API key authentication via FastAPI Security dependency.
"""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import get_settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    header_key: str | None = Security(_api_key_header),
) -> str:
    """
    FastAPI dependency that extracts and validates the API key.

    Priority:
      1. ``X-API-Key`` request header  (recommended for Postman / clients)
      2. ``GOOGLE_API_KEY`` from ``.env``  (server-side fallback)

    Raises ``401`` if no valid key can be resolved.
    """
    settings = get_settings()

    key = header_key or settings.google_api_key

    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Missing API key. Provide an 'X-API-Key' header or set "
                "GOOGLE_API_KEY in your .env file."
            ),
        )

    # Basic format check (Google API keys start with "AIza" and are ~39 chars)
    if len(key) < 20:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is too short — provide a valid Google Gemini key.",
        )

    return key
