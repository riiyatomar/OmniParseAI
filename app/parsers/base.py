"""
Abstract base parser and ParsedDocument data class.

All format-specific parsers must implement BaseParser.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ParsedDocument:
    """
    Result of parsing a file.

    Attributes:
        text:         Extracted raw text (for prose documents).
        rows_as_text: List of row-level text strings (for structured data like CSV).
        metadata:     File-level metadata (author, page count, schema, etc.).
        doc_type:     The document format identifier ("pdf", "csv", "odf").
        is_structured: True if the data is structured (CSV) vs prose (PDF/ODF).
    """

    text: str = ""
    rows_as_text: List[str] = field(default_factory=list)
    pages_text: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    doc_type: str = ""
    is_structured: bool = False


class BaseParser(ABC):
    """
    Interface all parsers must implement.

    Usage:
        parser = PdfParser()
        result: ParsedDocument = parser.parse("/path/to/file.pdf")
    """

    @abstractmethod
    def parse(self, file_path: str) -> ParsedDocument:
        """
        Parse the given file and return a ParsedDocument.

        Args:
            file_path: Absolute path to a temp file on disk.

        Returns:
            ParsedDocument with extracted text and metadata.

        Raises:
            FileParsingError: if the file cannot be parsed.
        """
        ...
