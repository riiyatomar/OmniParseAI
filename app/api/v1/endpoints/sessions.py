"""
Session management endpoints — list and delete sessions.
"""

from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.v1.deps import get_api_key
from app.services.ingestion import get_vs_manager

router = APIRouter()


# ── Response models ─────────────────────────────────────────────


class SessionInfo(BaseModel):
    session_id: str
    created_at: str
    chunk_count: int
    file_names: List[str]


class SessionsListResponse(BaseModel):
    status: str = "success"
    sessions: List[SessionInfo]


class DeleteResponse(BaseModel):
    status: str = "success"
    deleted: bool = True
    session_id: str


# ── Endpoints ───────────────────────────────────────────────────


@router.get("/sessions", response_model=SessionsListResponse, tags=["Sessions"])
def list_sessions(api_key: str = Depends(get_api_key)):
    """List all active sessions."""
    manager = get_vs_manager()
    raw = manager.list_sessions()
    sessions = [SessionInfo(**s) for s in raw]
    return SessionsListResponse(sessions=sessions)


@router.delete(
    "/sessions/{session_id}",
    response_model=DeleteResponse,
    tags=["Sessions"],
)
def delete_session(session_id: str, api_key: str = Depends(get_api_key)):
    """Delete a session and its FAISS index."""
    manager = get_vs_manager()
    manager.delete_session(session_id)
    return DeleteResponse(session_id=session_id)
