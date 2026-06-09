"""
Document ingestion endpoint — upload, parse, chunk, embed, index.
"""

from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel

from app.api.v1.deps import get_api_key
from app.services.ingestion import ingest_files

router = APIRouter()


# ── Response models ─────────────────────────────────────────────


class IngestResponse(BaseModel):
    status: str = "success"
    session_id: str
    chunk_count: int
    file_names: List[str]
    files_metadata: List[Dict]


# ── Endpoint ────────────────────────────────────────────────────


@router.post("/ingest", response_model=IngestResponse, tags=["Ingestion"])
async def ingest(
    files: List[UploadFile] = File(
        ..., description="One or more documents (PDF, CSV, ODF, Excel)"
    ),
    api_key: str = Depends(get_api_key),
):
    """
    Upload document(s), extract text, build FAISS vector index.

    Accepts PDF, CSV, and ODF files. Returns a ``session_id`` to use
    in ``/api/v1/chat`` for querying the uploaded documents.

    Authentication: pass ``X-API-Key`` header with your Google Gemini key.
    """
    result = await ingest_files(files, api_key)

    return IngestResponse(
        session_id=result["session_id"],
        chunk_count=result["chunk_count"],
        file_names=result["file_names"],
        files_metadata=result["files_metadata"],
    )
