"""
Format-aware chunking strategies.

- Prose text (PDF, ODF): RecursiveCharacterTextSplitter
- Structured data (CSV): Row-based grouping with schema injection
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """A single chunk of text with metadata."""

    text: str
    index: int
    metadata: dict = field(default_factory=dict)


def chunk_prose(
    text: str,
    *,
    source_file: str = "",
    extra_metadata: dict | None = None,
) -> List[Chunk]:
    """
    Split prose text (PDF / ODF) using recursive character splitting.

    Returns a list of Chunk objects with metadata.
    """
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " "],
    )

    raw_chunks = splitter.split_text(text)
    chunks: List[Chunk] = []

    for idx, raw in enumerate(raw_chunks):
        meta = {
            "source_file": source_file,
            "chunk_index": idx,
            "total_chunks": len(raw_chunks),
        }
        if extra_metadata:
            meta.update(extra_metadata)
        chunks.append(Chunk(text=raw, index=idx, metadata=meta))

    logger.info(
        "Chunked prose into %d chunks (size=%d, overlap=%d)",
        len(chunks),
        settings.chunk_size,
        settings.chunk_overlap,
    )
    return chunks


def chunk_structured(
    rows_as_text: List[str],
    *,
    schema_description: str = "",
    source_file: str = "",
) -> List[Chunk]:
    """
    Chunk structured data (CSV) by grouping N rows per chunk.

    Each chunk is prefixed with the schema description so the LLM
    always knows what the columns mean.
    """
    settings = get_settings()
    n = settings.csv_rows_per_chunk
    chunks: List[Chunk] = []
    total = (len(rows_as_text) + n - 1) // n  # ceil division

    for i in range(0, len(rows_as_text), n):
        batch = rows_as_text[i : i + n]
        body = "\n".join(batch)

        # Prepend schema to every chunk
        if schema_description:
            text = f"Schema: {schema_description}\n\nData:\n{body}"
        else:
            text = body

        idx = i // n
        chunks.append(
            Chunk(
                text=text,
                index=idx,
                metadata={
                    "source_file": source_file,
                    "chunk_index": idx,
                    "total_chunks": total,
                    "rows_in_chunk": len(batch),
                },
            )
        )

    logger.info(
        "Chunked structured data into %d chunks (%d rows/chunk)",
        len(chunks),
        n,
    )
    return chunks
