"""
File manager service — handles temp file lifecycle and validation.
"""

from __future__ import annotations

import logging
import os
import tempfile
from typing import Tuple

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import FileTooLarge

logger = logging.getLogger(__name__)


class FileManager:
    """Save uploaded files to temp directory and validate size."""

    @staticmethod
    async def save_upload(upload: UploadFile) -> Tuple[str, bytes]:
        """
        Save an UploadFile to a temp file and return (path, first_bytes).

        The caller is responsible for cleanup via ``cleanup(path)``.
        """
        settings = get_settings()
        max_bytes = settings.max_upload_size_mb * 1024 * 1024

        content = await upload.read()

        if len(content) > max_bytes:
            raise FileTooLarge(
                f"File '{upload.filename}' is {len(content) / 1024 / 1024:.1f} MB "
                f"— max allowed is {settings.max_upload_size_mb} MB."
            )

        # Determine suffix from original filename
        _, ext = os.path.splitext(upload.filename or "")
        suffix = ext or ".bin"

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        try:
            tmp.write(content)
            tmp.close()
        except Exception:
            tmp.close()
            if os.path.exists(tmp.name):
                os.remove(tmp.name)
            raise

        logger.info(
            "Saved upload '%s' to '%s' (%d bytes)",
            upload.filename,
            tmp.name,
            len(content),
        )
        return tmp.name, content[:2048]  # return first 2KB for MIME detection

    @staticmethod
    def cleanup(path: str) -> None:
        """Remove a temp file if it exists."""
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except OSError as exc:
            logger.warning("Failed to clean up temp file '%s': %s", path, exc)
