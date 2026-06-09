"""
Parser factory — routes MIME types to the correct parser.
"""

from __future__ import annotations

import logging
import mimetypes
from typing import Dict, Type

from app.core.exceptions import UnsupportedFileType
from app.parsers.base import BaseParser
from app.parsers.pdf import PdfParser
from app.parsers.csv_parser import CsvParser
from app.parsers.odf import OdfParser
from app.parsers.xlsx_parser import XlsxParser

logger = logging.getLogger(__name__)

# ── MIME type → parser mapping ──────────────────────────────────

_PARSER_MAP: Dict[str, Type[BaseParser]] = {
    "application/pdf": PdfParser,
    "text/csv": CsvParser,
    "application/vnd.oasis.opendocument.text": OdfParser,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": XlsxParser,
}

# ── Extension fallback (when MIME detection fails) ──────────────

_EXT_TO_MIME: Dict[str, str] = {
    ".pdf": "application/pdf",
    ".csv": "text/csv",
    ".odt": "application/vnd.oasis.opendocument.text",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


class ParserFactory:
    """
    Return the correct parser instance for a given file.

    Detection strategy:
      1. Try python-magic for MIME from file bytes (if installed).
      2. Fall back to mimetypes + extension mapping.
    """

    @staticmethod
    def detect_mime(file_path: str, file_bytes: bytes | None = None) -> str:
        """Detect the MIME type of a file."""

        # Strategy 1: python-magic (most reliable)
        if file_bytes:
            try:
                import magic  # python-magic

                mime = magic.from_buffer(file_bytes[:2048], mime=True)
                if mime and mime in _PARSER_MAP:
                    return mime
            except ImportError:
                pass  # python-magic not installed, fall through

        # Strategy 2: stdlib mimetypes (extension-based)
        mime, _ = mimetypes.guess_type(file_path)
        if mime and mime in _PARSER_MAP:
            return mime

        # Strategy 3: manual extension mapping
        for ext, mapped_mime in _EXT_TO_MIME.items():
            if file_path.lower().endswith(ext):
                return mapped_mime

        return "unknown"

    @classmethod
    def get(cls, file_path: str, file_bytes: bytes | None = None) -> BaseParser:
        """
        Return a parser instance for the given file.

        Args:
            file_path: Path to the file on disk.
            file_bytes: Optional raw bytes (first 2KB) for magic detection.

        Raises:
            UnsupportedFileType: if no parser matches.
        """
        mime = cls.detect_mime(file_path, file_bytes)

        parser_cls = _PARSER_MAP.get(mime)
        if parser_cls is None:
            raise UnsupportedFileType(mime, file_path)

        logger.info("Routing '%s' (mime=%s) to %s", file_path, mime, parser_cls.__name__)
        return parser_cls()
