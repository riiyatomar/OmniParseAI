"""
Centralized configuration using Pydantic BaseSettings.

All environment variables are validated and typed here.
Uses python-dotenv to load .env files automatically.
"""

import os
import platform
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Google Gemini ───────────────────────────────────────────
    google_api_key: str = Field(
        default="",
        description="Google Gemini API key (REQUIRED)",
    )
    gemini_model_name: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model for chat completions",
    )
    gemini_embedding_model: str = Field(
        default="models/gemini-embedding-001",
        description="Gemini model for text embeddings",
    )
    gemini_temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    gemini_max_tokens: int = Field(default=1024, ge=1)

    # ── OCR Paths ───────────────────────────────────────────────
    tesseract_cmd: str = Field(
        default=(
            r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            if platform.system() == "Windows"
            else "/usr/bin/tesseract"
        ),
    )
    poppler_path: str = Field(
        default=(
            r"C:\Program Files\poppler\Library\bin"
            if platform.system() == "Windows"
            else ""
        ),
    )

    # ── Vector Store ────────────────────────────────────────────
    storage_dir: str = Field(
        default="./storage/sessions",
        description="Base directory for session-isolated FAISS indices",
    )

    # ── Chunking ────────────────────────────────────────────────
    chunk_size: int = Field(default=1000, ge=100)
    chunk_overlap: int = Field(default=150, ge=0)
    csv_rows_per_chunk: int = Field(default=20, ge=1)

    # ── Embedding Pipeline ──────────────────────────────────────
    embed_batch_size: int = Field(default=20, ge=1)
    embed_retry_attempts: int = Field(default=5, ge=1)
    embed_retry_backoff: float = Field(default=3.0, ge=1.0)

    # ── Retrieval ───────────────────────────────────────────────
    retrieval_top_k: int = Field(default=5, ge=1)
    retrieval_score_threshold: float = Field(default=0.6, ge=0.0, le=1.0)

    # ── Upload Limits ───────────────────────────────────────────
    max_upload_size_mb: int = Field(default=50, ge=1)

    # ── Session Cache ───────────────────────────────────────────
    max_cached_sessions: int = Field(default=50, ge=1)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    Call get_settings.cache_clear() if you need to reload after env changes.
    """
    return Settings()
