"""
Ingestion service — orchestrates: upload → parse → clean → chunk → embed → index.
"""

from __future__ import annotations

import logging
import uuid
from typing import Dict, List

from fastapi import UploadFile

from app.core.exceptions import NoTextExtracted
from app.parsers.base import ParsedDocument
from app.parsers.factory import ParserFactory
from app.services.file_manager import FileManager
from app.utils.cleaning import is_garbage, normalize_text
from app.utils.chunking import Chunk, chunk_prose, chunk_structured
from app.vectorstore.embeddings import embed_chunks_batched
from app.vectorstore.manager import VectorStoreManager

logger = logging.getLogger(__name__)

# Singleton manager
_vs_manager = VectorStoreManager()


def get_vs_manager() -> VectorStoreManager:
    return _vs_manager


async def ingest_files(
    files: List[UploadFile],
    api_key: str,
) -> Dict:
    """
    Full ingestion pipeline:
      1. Save uploads to temp files
      2. Detect MIME and route to parser
      3. Normalize text
      4. Chunk (prose or structured)
      5. Embed and create FAISS index
      6. Return session metadata

    Returns a dict with session_id, chunk_count, file_names, etc.
    """
    session_id = uuid.uuid4().hex[:12]
    file_names: List[str] = []
    all_chunks: List[Chunk] = []
    all_metadata: List[Dict] = []
    temp_paths: List[str] = []

    try:
        for upload in files:
            # 1. Save to disk
            tmp_path, first_bytes = await FileManager.save_upload(upload)
            temp_paths.append(tmp_path)
            file_names.append(upload.filename or "unknown")

            # 2. Detect type and parse
            parser = ParserFactory.get(tmp_path, first_bytes)
            parsed: ParsedDocument = parser.parse(tmp_path)
            all_metadata.append(parsed.metadata)

            # 3. Clean and chunk
            if parsed.is_structured:
                # CSV → row-based chunking with schema
                schema = parsed.metadata.get("schema", "")
                chunks = chunk_structured(
                    parsed.rows_as_text,
                    schema_description=schema,
                    source_file=upload.filename or "",
                )
            else:
                # PDF / ODF → prose chunking
                cleaned = normalize_text(parsed.text)
                if not cleaned or is_garbage(cleaned):
                    logger.warning(
                        "File '%s' produced no usable text after cleaning",
                        upload.filename,
                    )
                    continue
                chunks = chunk_prose(
                    cleaned,
                    source_file=upload.filename or "",
                    extra_metadata=parsed.metadata,
                )

            all_chunks.extend(chunks)

    finally:
        # 6. Cleanup temp files
        for p in temp_paths:
            FileManager.cleanup(p)

    if not all_chunks:
        raise NoTextExtracted(
            "No text could be extracted from the uploaded file(s)."
        )

    # 4. Embed (probe first, then let FAISS batch internally)
    chunk_texts = [c.text for c in all_chunks]
    embeddings = embed_chunks_batched(chunk_texts, api_key)

    # 5. Create FAISS index
    manager = get_vs_manager()
    manager.create_index(
        session_id=session_id,
        chunks=chunk_texts,
        embeddings=embeddings,
        file_names=file_names,
    )

    result = {
        "session_id": session_id,
        "chunk_count": len(all_chunks),
        "file_names": file_names,
        "files_metadata": all_metadata,
    }
    logger.info("Ingestion complete: %s", result)
    return result
