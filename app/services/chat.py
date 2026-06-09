"""
Chat service — orchestrates: query → retrieve → context → LLM answer.
"""

from __future__ import annotations

import logging
from typing import Dict, List

from app.core.config import get_settings
from app.core.exceptions import SessionNotFound
from app.llm.gemini import ask_with_context
from app.services.ingestion import get_vs_manager
from app.vectorstore.embeddings import get_embeddings

logger = logging.getLogger(__name__)


def ask_question(
    session_id: str,
    question: str,
    api_key: str,
) -> Dict:
    """
    Retrieve relevant chunks from a session's FAISS index and answer
    the question using the Gemini LLM.

    Returns a dict with question, answer, sources, and model info.
    """
    settings = get_settings()
    manager = get_vs_manager()

    # Load the session's vector store
    embeddings = get_embeddings(api_key)

    if not manager.session_exists(session_id):
        raise SessionNotFound(f"Session '{session_id}' not found.")

    vs = manager.load_index(session_id, embeddings)

    # Retrieve relevant chunks with scores
    results = vs.similarity_search_with_score(question, k=settings.retrieval_top_k)

    if not results:
        return {
            "question": question,
            "answer": "No relevant content found in the uploaded documents.",
            "sources": [],
            "model": settings.gemini_model_name,
        }

    # Filter by score threshold (lower = better for L2 distance)
    # Note: For cosine similarity, higher is better — adjust if needed
    docs_with_scores = [(doc, float(score)) for doc, score in results]
    docs = [doc for doc, _ in docs_with_scores]

    # Sort by chunk order for coherent context
    docs.sort(key=lambda d: d.metadata.get("chunk_index", 0))

    # Generate answer
    answer = ask_with_context(question, docs, api_key)

    # Build sources list
    sources: List[Dict] = []
    for doc, score in docs_with_scores:
        sources.append({
            "content_preview": doc.page_content[:200] + "...",
            "score": round(score, 4),
            "metadata": doc.metadata,
        })

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "model": settings.gemini_model_name,
    }
