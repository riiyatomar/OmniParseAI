"""
📝 ODF Chat — Query OpenDocument (.odt) files with Google Gemini

- Streamlit UI with file upload support.
- Full document text preview (no truncation).
- Conversation history with CSV export.
- Uses new app/ architecture with retry logic.
"""

import logging
import sys
import os
import tempfile
from datetime import datetime

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings
from app.parsers.odf import OdfParser
from app.utils.cleaning import normalize_text
from app.llm.gemini import configure_gemini, ask_direct
from app.llm.prompts import ODF_PROMPT
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

# ── Page config ─────────────────────────────────────────────────
st.set_page_config(page_title="ODF Chat", page_icon="📝")

# ── Custom CSS ──────────────────────────────────────────────────
inject_chat_css()

# ── Session state ───────────────────────────────────────────────
init_api_key_state(settings)

if "odf_history" not in st.session_state:
    st.session_state.odf_history = []


# ── Header ──────────────────────────────────────────────────────
st.header("📝 Chat with ODF Documents")

# ── Sidebar ─────────────────────────────────────────────────────
with st.sidebar:
    # API key is loaded automatically from .env via init_api_key_state()
    if st.session_state.api_key:
        st.success("🔑 API Key loaded from .env", icon="✅")
    else:
        st.warning("⚠️ No API key found. Add GOOGLE_API_KEY to your .env file.")

    st.markdown("---")

    render_sidebar_history(
        "odf_history", "odf_chat",
        rerun_key="odf_rerun", reset_key="odf_reset",
    )

# ── Upload ODF ──────────────────────────────────────────────────
uploaded_odf = st.file_uploader("Upload an ODF (.odt) file", type=["odt"])

if uploaded_odf is not None:
    # Save to temp file (odfpy needs a real file path)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".odt")
    doc_text = ""
    try:
        tmp.write(uploaded_odf.read())
        tmp.close()
        parser = OdfParser()
        parsed = parser.parse(tmp.name)
        doc_text = normalize_text(parsed.text)
    except Exception as e:
        logger.exception("Failed to extract text from ODF")
        st.error(f"Failed to read the uploaded file: {e}")
    finally:
        if os.path.exists(tmp.name):
            os.remove(tmp.name)

    if not doc_text.strip():
        st.warning("No text could be extracted from the uploaded file.")
    else:
        # ── Metrics ─────────────────────────────────────────────
        col1, col2, col3 = st.columns(3)
        col1.metric("Characters", f"{len(doc_text):,}")
        col2.metric("Words", f"{len(doc_text.split()):,}")
        col3.metric("Paragraphs", f"{doc_text.count(chr(10)) + 1:,}")

        # ── Full Document Preview ───────────────────────────────
        st.subheader("📄 Complete Document Preview")
        with st.expander("Show full extracted text", expanded=True):
            st.text(doc_text)

        st.markdown("---")

        # ── Chat history ────────────────────────────────────────
        for q, a, *_ in st.session_state.odf_history:
            render_chat_message(q, a)

        # ── Question ────────────────────────────────────────────
        with st.form("odf_question_form", clear_on_submit=True):
            question = st.text_input(
                "Ask a question about this document",
                value="Summarize this document." if not st.session_state.odf_history else "",
            )
            submitted = st.form_submit_button("Ask Gemini", use_container_width=True)

        if submitted and question:
            if not st.session_state.api_key:
                st.warning("⚠️ No API key found. Add GOOGLE_API_KEY to your .env file.")
            else:
                with st.spinner("Thinking …"):
                    try:
                        configure_gemini(st.session_state.api_key)
                        answer = ask_direct(
                            question=question,
                            context_text=doc_text,
                            api_key=st.session_state.api_key,
                            prompt_template=ODF_PROMPT,
                        )
                    except Exception as e:
                        logger.exception("ODF Gemini error")
                        st.error(f"Error: {e}")
                        st.stop()

                st.session_state.odf_history.append(
                    (
                        question,
                        answer,
                        "Google Gemini",
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        uploaded_odf.name,
                    )
                )
                st.rerun()
else:
    st.info("👆 Upload an ODF (.odt) file to get started.")
