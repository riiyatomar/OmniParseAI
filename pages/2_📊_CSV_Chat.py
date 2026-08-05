"""
📊 CSV Chat — Query CSV data with Google Gemini

- Supports file upload with full data preview.
- Sends smart data summary + schema + statistics for accurate answers.
- Configurable row limit with high capacity.
- Conversation history with CSV export.
- Uses new app/ architecture with retry logic.
"""

import logging
import sys
import os
from datetime import datetime

import streamlit as st
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings
from app.llm.gemini import configure_gemini, ask_direct
from app.llm.prompts import CSV_PROMPT
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
st.set_page_config(page_title="CSV Chat", page_icon="📊")

# ── Custom CSS ──────────────────────────────────────────────────
inject_chat_css()

# ── Session state ───────────────────────────────────────────────
init_api_key_state(settings)

if "csv_history" not in st.session_state:
    st.session_state.csv_history = []


def _build_csv_stats(df: pd.DataFrame) -> str:
    """Build a comprehensive statistical summary of the full CSV."""
    lines = []
    lines.append(f"Total rows: {len(df):,}")
    lines.append(f"Total columns: {len(df.columns)}")
    lines.append(f"Column names: {', '.join(str(c) for c in df.columns)}")
    lines.append("")

    for col in df.columns:
        col_info = f"  Column '{col}' (dtype: {df[col].dtype})"
        null_count = df[col].isna().sum()
        non_null = len(df) - null_count
        col_info += f" — {non_null:,} non-null"
        if null_count > 0:
            col_info += f", {null_count:,} missing"

        if pd.api.types.is_numeric_dtype(df[col]):
            try:
                col_info += (
                    f"\n    min={df[col].min()}, max={df[col].max()}, "
                    f"mean={df[col].mean():.4f}, sum={df[col].sum():,.4f}, "
                    f"median={df[col].median()}, std={df[col].std():.4f}"
                )
            except Exception:
                pass
        elif pd.api.types.is_string_dtype(df[col]) or df[col].dtype == object:
            nunique = df[col].nunique()
            col_info += f"\n    {nunique:,} unique values"
            if nunique <= 20:
                top_vals = df[col].value_counts().head(10)
                vals_str = ", ".join(f"'{v}': {c}" for v, c in top_vals.items())
                col_info += f"\n    Top values: {vals_str}"

        lines.append(col_info)

    return "\n".join(lines)


# ── Header ──────────────────────────────────────────────────────
st.header("📊 Chat with CSV Data")

# ── Sidebar ─────────────────────────────────────────────────────
with st.sidebar:
    # API key is loaded automatically from .env via init_api_key_state()
    if st.session_state.api_key:
        st.success("🔑 API Key loaded from .env", icon="✅")
    else:
        st.warning("⚠️ No API key found. Add GOOGLE_API_KEY to your .env file.")

    st.markdown("---")

    max_rows = st.slider(
        "Sample rows to include in prompt",
        min_value=50,
        max_value=5000,
        value=500,
        step=50,
        help=(
            "Number of sample rows sent alongside the full statistical summary. "
            "More rows = better context but higher token cost."
        ),
    )

    st.markdown("---")

    render_sidebar_history(
        "csv_history", "csv_chat",
        rerun_key="csv_rerun", reset_key="csv_reset",
    )

# ── Upload CSV ──────────────────────────────────────────────────
uploaded_csv = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_csv is not None:
    try:
        df = pd.read_csv(uploaded_csv)
    except Exception as e:
        st.error(f"Failed to parse CSV: {e}")
        st.stop()

    # ── Metrics ─────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rows", f"{len(df):,}")
    col2.metric("Columns", len(df.columns))
    col3.metric("Non-null Cells", f"{df.notna().sum().sum():,}")
    col4.metric("Size", f"{uploaded_csv.size / 1024:.1f} KB")

    # ── Complete Data Preview ───────────────────────────────────
    st.subheader("📋 Complete Data Preview")
    st.caption(f"Columns: {', '.join(str(c) for c in df.columns)}")
    st.dataframe(df, use_container_width=True, height=500)

    # Quick stats for numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        with st.expander("📊 Quick Statistics", expanded=False):
            st.dataframe(
                df[numeric_cols].describe().round(2),
                use_container_width=True,
            )

    st.markdown("---")

    # ── Chat history ────────────────────────────────────────────
    for q, a, *_ in st.session_state.csv_history:
        render_chat_message(q, a)

    # ── Question ────────────────────────────────────────────────
    with st.form("csv_question_form", clear_on_submit=True):
        question = st.text_input("Ask a question about this data")
        submitted = st.form_submit_button("Ask", use_container_width=True)

    if submitted and question:
        if not st.session_state.api_key:
            st.warning("⚠️ No API key found. Add GOOGLE_API_KEY to your .env file.")
        else:
            # Build context with full statistics + sample data
            stats_summary = _build_csv_stats(df)

            sample_df = df.head(max_rows)
            csv_text = sample_df.to_csv(index=False)

            context = (
                f"=== FULL DATASET STATISTICS ===\n"
                f"{stats_summary}\n\n"
                f"=== SAMPLE DATA (first {len(sample_df)} of {len(df):,} rows) ===\n"
                f"{csv_text}"
            )

            # Add tail for large datasets
            if len(df) > max_rows and len(df) > 20:
                tail = df.tail(min(10, max_rows // 10))
                context += f"\n\n=== LAST {len(tail)} ROWS ===\n{tail.to_csv(index=False)}"

            with st.spinner("Analysing data …"):
                try:
                    configure_gemini(st.session_state.api_key)
                    answer = ask_direct(
                        question=question,
                        context_text=context,
                        api_key=st.session_state.api_key,
                        prompt_template=CSV_PROMPT,
                    )
                except Exception as e:
                    logger.exception("CSV Gemini error")
                    st.error(f"Error: {e}")
                    st.stop()

            st.session_state.csv_history.append(
                (
                    question,
                    answer,
                    "Google Gemini",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    uploaded_csv.name,
                )
            )
            st.rerun()

else:
    st.info("👆 Upload a CSV file to get started.")
