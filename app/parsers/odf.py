"""
ODF (OpenDocument Text) parser using odfpy.
"""

import logging

from app.core.exceptions import FileParsingError
from app.parsers.base import BaseParser, ParsedDocument

logger = logging.getLogger(__name__)


class OdfParser(BaseParser):
    """
    Extract text from .odt (OpenDocument) files.

    Uses odfpy to walk <text:p> elements and concatenate paragraphs.
    """

    def parse(self, file_path: str) -> ParsedDocument:
        try:
            from odf.opendocument import load as odf_load
            from odf.text import P
            from odf import teletype
        except ImportError as exc:
            raise FileParsingError(
                "odfpy is not installed. Run: pip install odfpy"
            ) from exc

        try:
            doc = odf_load(file_path)
        except Exception as exc:
            raise FileParsingError(
                f"Cannot open ODF file: {exc}"
            ) from exc

        paragraphs: list[str] = []

        for element in doc.getElementsByType(P):
            text = teletype.extractText(element).strip()
            if text:
                paragraphs.append(text)

        full_text = "\n\n".join(paragraphs)

        metadata = {
            "paragraphs": len(paragraphs),
            "characters": len(full_text),
        }

        logger.info(
            "Parsed ODF: %d paragraphs, %d chars",
            len(paragraphs),
            len(full_text),
        )

        return ParsedDocument(
            text=full_text,
            metadata=metadata,
            doc_type="odf",
            is_structured=False,
        )
