"""
📄 PDF Chat — Multi-PDF RAG with Google Gemini

- Page-by-page reading with per-page summary generation.
- Vector store is cached in session state — PDFs are only embedded once.
- Uses new app/ modular architecture.
- Proper temp-file cleanup in finally blocks.
"""

import logging
import sys
import os
from datetime import datetime

import streamlit as st
import pandas as pd

# ── Ensure project root is on sys.path so app/ modules resolve ──
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings
from app.parsers.pdf import PdfParser
from app.utils.cleaning import normalize_text
from app.utils.chunking import chunk_prose
from app.vectorstore.embeddings import get_embeddings
from app.vectorstore.manager import VectorStoreManager
from app.llm.gemini import configure_gemini, ask_with_context, ask_direct
from app.llm.prompts import QA_PROMPT
from utils.styles import (
    inject_chat_css,
    render_chat_message,
    init_api_key_state,
    render_sidebar_history,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ── Load settings ───────────────────────────────────────────────
settings = get_settings()
_vs_manager = VectorStoreManager()

# ── Page config ─────────────────────────────────────────────────
st.set_page_config(page_title="PDF Chat", page_icon="📄")

# ── Custom CSS ──────────────────────────────────────────────────
inject_chat_css()

# ── Session state defaults ──────────────────────────────────────
init_api_key_state(settings)

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "pdf_docs" not in st.session_state:
    st.session_state.pdf_docs = []
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "pdf_names_hash" not in st.session_state:
    st.session_state.pdf_names_hash = ""
if "pdf_pages_text" not in st.session_state:
    st.session_state.pdf_pages_text = []  # List of (page_num, page_text, source_file)
if "pdf_page_summaries" not in st.session_state:
    st.session_state.pdf_page_summaries = {}  # {page_key: summary}


# ── Helpers ─────────────────────────────────────────────────────
def _pdfs_fingerprint(pdf_docs) -> str:
    """Return a simple fingerprint string for the uploaded PDFs."""
    return "|".join(sorted(f"{p.name}:{p.size}" for p in pdf_docs))


def process_question(user_question: str) -> None:
    """Run similarity search + LLM for the given question."""
    api_key = st.session_state.api_key
    vs = st.session_state.vector_store

    if vs is None:
        st.warning("Please upload and process PDF files first.")
        return

    try:
        docs = vs.similarity_search(user_question, k=settings.retrieval_top_k)
        answer = ask_with_context(user_question, docs, api_key, QA_PROMPT)
    except Exception as e:
        logger.exception("QA error")
        st.error(f"Error during model invocation: {e}")
        return

    st.session_state.conversation_history.append(
        (
            user_question,
            answer,
            "Google Gemini",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ", ".join(p.name for p in st.session_state.pdf_docs),
        )
    )


def _extract_and_index(pdf_docs, api_key: str):
    """Parse PDFs, chunk, embed, and create a vector store. Also store per-page text."""
    import tempfile

    parser = PdfParser()
    all_text = ""
    all_pages = []  # (page_num, text, source_file)

    for pdf in pdf_docs:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        try:
            tmp.write(pdf.getbuffer())
            tmp.close()
            parsed = parser.parse(tmp.name)
            all_text += parsed.text + "\n\n"

            # Store per-page text
            if hasattr(parsed, 'pages_text') and parsed.pages_text:
                for i, page_text in enumerate(parsed.pages_text, start=1):
                    all_pages.append((i, page_text, pdf.name))
            else:
                # Fallback — split combined text by double-newline as rough pages
                pages = parsed.text.split("\n\n")
                for i, page_text in enumerate(pages, start=1):
                    if page_text.strip():
                        all_pages.append((i, page_text.strip(), pdf.name))
        except Exception:
            logger.exception("Failed to extract text from %s", pdf.name)
            raise
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

    cleaned = normalize_text(all_text)
    if not cleaned.strip():
        return None, 0, []

    chunks = chunk_prose(cleaned, source_file="uploaded_pdfs")
    chunk_texts = [c.text for c in chunks]

    embeddings = get_embeddings(api_key)
    from langchain_community.vectorstores import FAISS
    vs = FAISS.from_texts(chunk_texts, embedding=embeddings)

    return vs, len(chunks), all_pages


# ── Header ──────────────────────────────────────────────────────
st.header("📄 Chat with Multiple PDFs")

# ── Sidebar ─────────────────────────────────────────────────────
with st.sidebar:
    st.title("Menu")

    # API key is loaded automatically from .env via init_api_key_state()
    if st.session_state.api_key:
        st.success("🔑 API Key loaded from .env", icon="✅")
    else:
        st.warning("⚠️ No API key found. Add GOOGLE_API_KEY to your .env file.")

    st.markdown("---")

    st.subheader("📁 Upload PDFs")
    st.session_state.pdf_docs = st.file_uploader(
        "Upload your PDF files",
        accept_multiple_files=True,
        type=["pdf"],
        label_visibility="visible",
    )

    if st.button("🔄 Submit & Process", use_container_width=True):
        if not st.session_state.api_key:
            st.warning("⚠️ No API key found. Add GOOGLE_API_KEY to your .env file.")
        elif not st.session_state.pdf_docs:
            st.warning("Please upload PDF files.")
        else:
            fp = _pdfs_fingerprint(st.session_state.pdf_docs)
            if fp == st.session_state.pdf_names_hash and st.session_state.vector_store:
                st.info("Documents already processed — ready for questions!")
            else:
                with st.spinner("Extracting text & building index …"):
                    try:
                        configure_gemini(st.session_state.api_key)
                        vs, chunk_count, pages = _extract_and_index(
                            st.session_state.pdf_docs,
                            st.session_state.api_key,
                        )
                        if vs is None:
                            st.warning(
                                "No text could be extracted. "
                                "The files may be empty or unsupported."
                            )
                        else:
                            st.session_state.vector_store = vs
                            st.session_state.pdf_names_hash = fp
                            st.session_state.pdf_pages_text = pages
                            st.session_state.pdf_page_summaries = {}
                            st.success(
                                f"✅ Processed {len(st.session_state.pdf_docs)} "
                                f"file(s) — {chunk_count} chunks indexed, "
                                f"{len(pages)} pages extracted."
                            )
                    except Exception as e:
                        logger.exception("PDF processing error")
                        st.error(f"❌ Processing failed: {e}")

    st.markdown("---")

    # PDF page uses "conversation_history" key with extra column "PDF Name"
    st.subheader("📜 History")
    col1, col2 = st.columns(2)
    if col1.button("Rerun"):
        st.rerun()
    if col2.button("Reset"):
        st.session_state.conversation_history = []
        st.session_state.vector_store = None
        st.session_state.pdf_names_hash = ""
        st.session_state.pdf_pages_text = []
        st.session_state.pdf_page_summaries = {}
        st.rerun()

    if st.session_state.conversation_history:
        df = pd.DataFrame(
            st.session_state.conversation_history,
            columns=["Question", "Answer", "Model", "Timestamp", "PDF Name"],
        )
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="⬇️ Download History CSV",
            data=csv_data,
            file_name="conversation_history.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ── Page-by-Page Reader ────────────────────────────────────────
if st.session_state.pdf_pages_text:
    st.markdown("---")
    st.subheader("📖 Page-by-Page Reader")

    pages = st.session_state.pdf_pages_text

    # Group pages by source file
    source_files = sorted(set(p[2] for p in pages))

    if len(source_files) > 1:
        selected_file = st.selectbox(
            "Select PDF", options=["All Files"] + source_files
        )
        if selected_file != "All Files":
            pages = [p for p in pages if p[2] == selected_file]

    # Page navigator
    total_pages = len(pages)
    st.caption(f"📄 {total_pages} pages available")

    page_idx = st.slider(
        "Page",
        min_value=1,
        max_value=total_pages,
        value=1,
        key="pdf_page_slider",
    )

    current_page = pages[page_idx - 1]
    page_num, page_text, source_file = current_page
    page_key = f"{source_file}__page_{page_num}"

    # Page info
    st.markdown(f"**Page {page_num}** from *{source_file}*  ·  {len(page_text):,} characters")

    # Page content preview
    with st.expander("📄 Page Content", expanded=True):
        st.text(page_text if page_text.strip() else "(No text extracted from this page)")

    # Generate summary button
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📝 Generate Page Summary", use_container_width=True, key="gen_summary"):
            if not st.session_state.api_key:
                st.warning("⚠️ No API key found. Add GOOGLE_API_KEY to your .env file.")
            elif not page_text.strip():
                st.warning("No text on this page to summarize.")
            else:
                with st.spinner("Generating summary …"):
                    try:
                        configure_gemini(st.session_state.api_key)
                        summary_prompt = (
                            "Provide a clear and comprehensive summary of the following "
                            "document page. Include all key points, facts, and important details.\n\n"
                            "Page Content:\n{context}\n\n"
                            "Summary:"
                        )
                        summary = ask_direct(
                            question="Summarize this page",
                            context_text=page_text,
                            api_key=st.session_state.api_key,
                            prompt_template=summary_prompt,
                        )
                        st.session_state.pdf_page_summaries[page_key] = summary
                    except Exception as e:
                        st.error(f"Error generating summary: {e}")

    with col_b:
        if st.button("❓ Ask About This Page", use_container_width=True, key="ask_page"):
            st.session_state["_ask_page_mode"] = True

    # Display cached summary if available
    if page_key in st.session_state.pdf_page_summaries:
        st.success("**Page Summary:**")
        st.markdown(st.session_state.pdf_page_summaries[page_key])

    # Per-page question form
    if st.session_state.get("_ask_page_mode"):
        with st.form("page_question_form", clear_on_submit=True):
            page_question = st.text_input("Ask a question about this specific page")
            page_submitted = st.form_submit_button("Ask", use_container_width=True)

        if page_submitted and page_question:
            if not st.session_state.api_key:
                st.warning("⚠️ No API key found. Add GOOGLE_API_KEY to your .env file.")
            else:
                with st.spinner("Thinking …"):
                    try:
                        configure_gemini(st.session_state.api_key)
                        page_answer = ask_direct(
                            question=page_question,
                            context_text=f"Page {page_num} from {source_file}:\n\n{page_text}",
                            api_key=st.session_state.api_key,
                            prompt_template=QA_PROMPT,
                        )
                        render_chat_message(page_question, page_answer)
                    except Exception as e:
                        st.error(f"Error: {e}")


# ── Full Document Chat ──────────────────────────────────────────
st.markdown("---")
st.subheader("💬 Chat with Full Document")

# ── Chat history ────────────────────────────────────────────────
for q, a, *_ in st.session_state.conversation_history:
    render_chat_message(q, a)

# ── Question input ──────────────────────────────────────────────
with st.form("question_form", clear_on_submit=True):
    user_question = st.text_input("Ask a question from the PDF files")
    submitted = st.form_submit_button("Ask", use_container_width=True)

if submitted and user_question:
    if not st.session_state.api_key:
        st.warning("⚠️ No API key found. Add GOOGLE_API_KEY to your .env file.")
    elif st.session_state.vector_store is None:
        st.warning("Please upload and process PDF files first.")
    else:
        with st.spinner("Thinking …"):
            process_question(user_question)
        st.rerun()
