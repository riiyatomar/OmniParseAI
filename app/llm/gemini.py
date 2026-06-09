"""
Google Gemini LLM wrapper with configuration and retry logic.
"""

from __future__ import annotations

import logging
import os
import time
from typing import List

import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document

from app.core.config import get_settings
from app.core.exceptions import LLMError
from app.llm.prompts import QA_PROMPT, CSV_PROMPT

logger = logging.getLogger(__name__)


def configure_gemini(api_key: str) -> None:
    """Configure the google.generativeai SDK + set env var."""
    os.environ["GOOGLE_API_KEY"] = api_key
    genai.configure(api_key=api_key)


def get_llm(api_key: str) -> ChatGoogleGenerativeAI:
    """Return a configured ChatGoogleGenerativeAI instance."""
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model_name,
        google_api_key=api_key,
        temperature=settings.gemini_temperature,
        max_tokens=settings.gemini_max_tokens,
    )


# ── Private retry helper ───────────────────────────────────────


def _call_with_retry(model, prompt: str) -> str:
    """
    Call model.generate_content with exponential backoff retry.

    Handles rate limits (429), invalid API keys, and generic errors.
    """
    settings = get_settings()

    for attempt in range(1, settings.embed_retry_attempts + 1):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as exc:
            err_str = str(exc).lower()

            # API key error — don't retry
            if "api key" in err_str or "invalid" in err_str:
                raise LLMError(f"Invalid API key: {exc}") from exc

            # Last attempt — give up
            if attempt == settings.embed_retry_attempts:
                raise LLMError(
                    f"LLM generation failed after {attempt} attempts: {exc}"
                ) from exc

            # Determine wait time
            wait = settings.embed_retry_backoff ** attempt
            if "rate" in err_str or "429" in err_str:
                logger.warning(
                    "Rate limited on LLM call, waiting %.1fs "
                    "(attempt %d/%d)",
                    wait, attempt, settings.embed_retry_attempts,
                )
            else:
                logger.warning("LLM error (attempt %d): %s", attempt, exc)
            time.sleep(wait)

    raise LLMError("LLM generation failed after all retries.")


# ── Public API ──────────────────────────────────────────────────


def ask_with_context(
    question: str,
    context_docs: List[Document],
    api_key: str,
    prompt_template: str = QA_PROMPT,
) -> str:
    """
    Send a question with retrieved context to Gemini and return the answer.

    Uses the raw google.generativeai SDK for simplicity and reliability.
    """
    settings = get_settings()
    configure_gemini(api_key)

    # Build context string from retrieved documents
    context_parts = []
    for doc in context_docs:
        source = doc.metadata.get("source_file", "Unknown")
        page = doc.metadata.get("page_number", "N/A")
        context_parts.append(
            f"[Source: {source}, Page: {page}]\n{doc.page_content}"
        )
    context = "\n\n---\n\n".join(context_parts)

    prompt = prompt_template.format(context=context, question=question)
    model = genai.GenerativeModel(settings.gemini_model_name)
    return _call_with_retry(model, prompt)


def ask_direct(
    question: str,
    context_text: str,
    api_key: str,
    prompt_template: str = CSV_PROMPT,
) -> str:
    """
    Ask a question with raw text context (used for CSV / ODF without vector search).
    """
    settings = get_settings()
    configure_gemini(api_key)

    prompt = prompt_template.format(context=context_text, question=question)
    model = genai.GenerativeModel(settings.gemini_model_name)
    return _call_with_retry(model, prompt)
