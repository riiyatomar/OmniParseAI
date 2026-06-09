"""
Batched embedding pipeline with retry / exponential backoff.
"""

from __future__ import annotations

import logging
import os
import time
from typing import List

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import get_settings
from app.core.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


def get_embeddings(api_key: str) -> GoogleGenerativeAIEmbeddings:
    """
    Return a configured GoogleGenerativeAIEmbeddings instance.

    Also sets the environment variable as a fallback for libraries
    that read GOOGLE_API_KEY from the environment directly.
    """
    settings = get_settings()
    os.environ["GOOGLE_API_KEY"] = api_key

    return GoogleGenerativeAIEmbeddings(
        model=settings.gemini_embedding_model,
        google_api_key=api_key,
    )


def embed_chunks_batched(
    chunks: List[str],
    api_key: str,
) -> GoogleGenerativeAIEmbeddings:
    """
    Validate that embedding works by embedding a small probe,
    then return the embeddings object for FAISS to use internally.

    Raises EmbeddingError on failure.
    """
    settings = get_settings()
    emb = get_embeddings(api_key)

    # Probe with first chunk to catch auth/quota errors early
    for attempt in range(1, settings.embed_retry_attempts + 1):
        try:
            _ = emb.embed_query(chunks[0][:200])
            logger.info("Embedding probe successful (attempt %d)", attempt)
            return emb
        except Exception as exc:
            err_str = str(exc).lower()
            if "rate" in err_str or "429" in err_str:
                wait = settings.embed_retry_backoff ** attempt
                logger.warning(
                    "Rate limited on embed probe, waiting %.1fs (attempt %d/%d)",
                    wait,
                    attempt,
                    settings.embed_retry_attempts,
                )
                time.sleep(wait)
            elif "api key" in err_str or "invalid" in err_str or "401" in err_str:
                raise EmbeddingError(
                    f"Invalid API key for embeddings: {exc}"
                ) from exc
            else:
                if attempt == settings.embed_retry_attempts:
                    raise EmbeddingError(
                        f"Embedding failed after {attempt} attempts: {exc}"
                    ) from exc
                wait = settings.embed_retry_backoff ** attempt
                logger.warning(
                    "Embed probe failed (attempt %d/%d): %s — retrying in %.1fs",
                    attempt,
                    settings.embed_retry_attempts,
                    exc,
                    wait,
                )
                time.sleep(wait)

    raise EmbeddingError("Embedding probe failed after all retries.")
