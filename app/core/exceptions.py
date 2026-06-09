"""
Custom exception classes with HTTP status code mapping.

These are raised inside services/core and caught by the global
exception handler in main.py to return structured JSON errors.
"""

from fastapi import HTTPException, status


class AppError(Exception):
    """Base class for all application errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "An unexpected error occurred."

    def __init__(self, detail: str | None = None, **kwargs):
        self.detail = detail or self.__class__.detail
        self.extra = kwargs
        super().__init__(self.detail)


# ── File Handling ───────────────────────────────────────────────


class UnsupportedFileType(AppError):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    detail = "Unsupported file type."

    def __init__(self, mime: str, filename: str):
        super().__init__(
            f"Unsupported file type '{mime}' for file '{filename}'. "
            "Supported: PDF, CSV, ODF, Excel (.xlsx)."
        )


class FileTooLarge(AppError):
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    detail = "File exceeds the maximum allowed size."


class FileParsingError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Failed to parse the uploaded file."


class NoTextExtracted(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "No text could be extracted from the uploaded file(s)."


# ── Sessions ────────────────────────────────────────────────────


class SessionNotFound(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Session not found."


# ── Embedding / LLM ────────────────────────────────────────────


class EmbeddingError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    detail = "Embedding generation failed."


class LLMError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    detail = "LLM generation failed."


class RateLimitExceeded(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    detail = "Upstream API rate limit exceeded. Please retry later."
