"""
Chat endpoint — query uploaded documents.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.v1.deps import get_api_key
from app.services.chat import ask_question

router = APIRouter()


# ── Request / Response models ───────────────────────────────────


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from /ingest")
    question: str = Field(..., min_length=1, description="Your question")


class SourceInfo(BaseModel):
    content_preview: str
    score: float
    metadata: Dict


class ChatResponse(BaseModel):
    status: str = "success"
    question: str
    answer: str
    sources: List[SourceInfo] = []
    model: str


# ── Endpoint ────────────────────────────────────────────────────


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat(
    body: ChatRequest,
    api_key: str = Depends(get_api_key),
):
    """
    Ask a question about previously uploaded documents.

    Requires a valid ``session_id`` from a prior ``/ingest`` call.
    Authentication: pass ``X-API-Key`` header with your Google Gemini key.
    """
    result = ask_question(
        session_id=body.session_id,
        question=body.question,
        api_key=api_key,
    )

    return ChatResponse(
        question=result["question"],
        answer=result["answer"],
        sources=[SourceInfo(**s) for s in result.get("sources", [])],
        model=result["model"],
    )
