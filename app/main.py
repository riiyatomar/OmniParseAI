"""
FastAPI application factory.

Creates the app with:
  - CORS middleware
  - Global exception handlers (structured JSON errors)
  - Versioned API router (/api/v1)
  - Swagger UI with API key header
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.exceptions import AppError

# ── Load .env before anything else ──────────────────────────────
load_dotenv()

# ── Logging ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("app")


def create_app() -> FastAPI:
    """Build and return the FastAPI application."""

    application = FastAPI(
        title="Document Chat Hub API",
        description=(
            "Production-grade RAG API for chatting with PDF, CSV, and ODF "
            "documents.  Upload files via `/api/v1/ingest`, then query them "
            "via `/api/v1/chat`."
        ),
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ────────────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Global exception handlers ───────────────────────────────

    @application.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        """Handle all custom AppError subclasses."""
        logger.error("AppError [%d]: %s", exc.status_code, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "data": None,
                "error": {
                    "type": type(exc).__name__,
                    "message": exc.detail,
                },
            },
        )

    @application.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        """Catch-all for unhandled exceptions — never leak stack traces."""
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "data": None,
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                },
            },
        )

    # ── Mount router ────────────────────────────────────────────
    application.include_router(api_router)

    @application.get("/", include_in_schema=False)
    def root():
        return {"message": "Document Chat Hub API v2.0 — visit /docs for Swagger UI."}

    logger.info("Document Chat Hub API v2.0 initialized")
    return application


# ── Module-level app for uvicorn ────────────────────────────────
app = create_app()
