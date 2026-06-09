"""
Session-isolated FAISS index manager with LRU caching.

Each upload session gets its own directory with its own FAISS index,
preventing overwrites between concurrent users/sessions.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Dict, List, Optional

from langchain_community.vectorstores import FAISS

from app.core.config import get_settings
from app.core.exceptions import SessionNotFound

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """
    Manage session-isolated FAISS indices.

    Features:
      - Each session has a dedicated directory under ``storage/sessions/{id}/``
      - LRU cache keeps recently-used indices in memory
      - manifest.json tracks session metadata
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.base_dir = settings.storage_dir
        self._max_cache = settings.max_cached_sessions
        # OrderedDict for LRU behaviour
        self._cache: OrderedDict[str, FAISS] = OrderedDict()
        os.makedirs(self.base_dir, exist_ok=True)

    # ── Path helpers ────────────────────────────────────────────

    def _session_dir(self, session_id: str) -> str:
        return os.path.join(self.base_dir, session_id)

    def _manifest_path(self, session_id: str) -> str:
        return os.path.join(self._session_dir(session_id), "manifest.json")

    # ── CRUD ────────────────────────────────────────────────────

    def create_index(
        self,
        session_id: str,
        chunks: List[str],
        embeddings,
        file_names: List[str] | None = None,
    ) -> FAISS:
        """Build a new FAISS index and persist it."""
        path = self._session_dir(session_id)
        os.makedirs(path, exist_ok=True)

        vs = FAISS.from_texts(chunks, embedding=embeddings)
        vs.save_local(path)

        # Write manifest
        manifest = {
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "chunk_count": len(chunks),
            "file_names": file_names or [],
        }
        with open(self._manifest_path(session_id), "w") as f:
            json.dump(manifest, f, indent=2)

        # Cache it
        self._put_cache(session_id, vs)
        logger.info("Created FAISS index for session '%s' (%d chunks)", session_id, len(chunks))
        return vs

    def load_index(self, session_id: str, embeddings) -> FAISS:
        """Load a session's FAISS index (cache-first)."""
        # Check cache
        if session_id in self._cache:
            self._cache.move_to_end(session_id)
            return self._cache[session_id]

        path = self._session_dir(session_id)
        if not os.path.isdir(path):
            raise SessionNotFound(f"Session '{session_id}' does not exist.")

        vs = FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
        self._put_cache(session_id, vs)
        logger.info("Loaded FAISS index for session '%s'", session_id)
        return vs

    def delete_session(self, session_id: str) -> None:
        """Remove a session's index from disk and cache."""
        path = self._session_dir(session_id)
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        self._cache.pop(session_id, None)
        logger.info("Deleted session '%s'", session_id)

    def list_sessions(self) -> List[Dict]:
        """Return metadata for all sessions."""
        sessions = []
        if not os.path.isdir(self.base_dir):
            return sessions

        for name in os.listdir(self.base_dir):
            manifest_path = os.path.join(self.base_dir, name, "manifest.json")
            if os.path.isfile(manifest_path):
                with open(manifest_path) as f:
                    sessions.append(json.load(f))

        return sessions

    def session_exists(self, session_id: str) -> bool:
        return os.path.isdir(self._session_dir(session_id))

    # ── LRU Cache ───────────────────────────────────────────────

    def _put_cache(self, session_id: str, vs: FAISS) -> None:
        self._cache[session_id] = vs
        self._cache.move_to_end(session_id)
        # Evict oldest if over limit
        while len(self._cache) > self._max_cache:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("Evicted session '%s' from cache", evicted_key)
