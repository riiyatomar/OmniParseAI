"""
📈 Excel Chat — Query Excel workbooks with Google Gemini

- Supports .xlsx / .xls file upload.
- Reads ALL data from ALL sheets — no truncation.
- Sends full statistical summary + schema + sample data for accurate answers.
- Configurable sample-row limit for the prompt.
- Complete data preview with pagination.
- Conversation history with CSV export.
- Uses new app/ architecture with retry logic.
"""

import logging
import re
import sys
import os
from datetime import datetime

import streamlit as st
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings
from app.llm.gemini import configure_gemini, ask_direct
from app.llm.prompts import EXCEL_PROMPT
from utils.styles import (
    inject_chat_css,
    render_chat_message,
    init_api_key_state,
    render_sidebar_history,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Regex to match pandas auto-generated "Unnamed: X" column names
_UNNAMED_RE = re.compile(r"^Unnamed:\s*\d+$")


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean a raw DataFrame: drop empty rows/cols, remove Unnamed artefacts."""
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")
    if df.empty:
        return df
    # Drop "Unnamed" columns that are entirely empty
    cols_to_drop = [
        col for col in df.columns
        if _UNNAMED_RE.match(str(col)) and df[col].notna().mean() <= 0.05
    ]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
    # Rename remaining "Unnamed" columns that have data to "Column_N"
    rename_map = {}
    for col in df.columns:
        if _UNNAMED_RE.match(str(col)):
            idx = str(col).split(":")[-1].strip()
            rename_map[col] = f"Column_{idx}"
    if rename_map:
        df = df.rename(columns=rename_map)
    # Strip whitespace from string columns
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip().replace("nan", pd.NA)
    df = df.dropna(how="all")
    df = df.reset_index(drop=True)
    return df


def _build_statistical_summary(df: pd.DataFrame, sheet_name: str) -> str:
    """Build a comprehensive statistical summary of the full dataframe."""
    lines = []
    lines.append(f"=== Sheet: {sheet_name} ===")
    lines.append(f"Total rows: {len(df):,}")
    lines.append(f"Total columns: {len(df.columns)}")
    lines.append(f"Column names: {', '.join(str(c) for c in df.columns)}")
    lines.append("")

    # Column details with stats
    for col in df.columns:
        col_info = f"  Column '{col}' (dtype: {df[col].dtype})"
        null_count = df[col].isna().sum()
        non_null = len(df) - null_count
        col_info += f" — {non_null:,} non-null values"
        if null_count > 0:
            col_info += f", {null_count:,} missing"

        if pd.api.types.is_numeric_dtype(df[col]):
            desc = df[col].describe()
            col_info += (
                f"\n    min={desc.get('min', 'N/A')}, "
                f"max={desc.get('max', 'N/A')}, "
                f"mean={desc.get('mean', 'N/A'):.4f}, "
                f"sum={df[col].sum():,.4f}, "
                f"median={df[col].median()}, "
                f"std={desc.get('std', 'N/A'):.4f}"
            )
        elif pd.api.types.is_string_dtype(df[col]) or df[col].dtype == object:
            nunique = df[col].nunique()
            col_info += f"\n    {nunique:,} unique values"
            if nunique <= 20:
                top_vals = df[col].value_counts().head(10)
                vals_str = ", ".join(f"'{v}': {c}" for v, c in top_vals.items())
                col_info += f"\n    Top values: {vals_str}"

        lines.append(col_info)

    return "\n".join(lines)


def _build_full_context(all_sheets: dict, selected_sheet: str, max_sample_rows: int) -> str:
    """Build the complete context with statistical summaries + sample data."""
    context_parts = []

    if selected_sheet == "All Sheets":
        sheets_to_process = all_sheets
    else:
        sheets_to_process = {selected_sheet: all_sheets[selected_sheet]}

    for name, sheet_df in sheets_to_process.items():
        # 1. Full statistical summary (covers ALL rows)
        stats = _build_statistical_summary(sheet_df, name)
        context_parts.append(stats)

        # 2. Sample data rows
        sample = sheet_df.head(max_sample_rows)
        csv_text = sample.to_csv(index=False)
        context_parts.append(
            f"\nSample data from '{name}' (first {len(sample)} of {len(sheet_df):,} rows):\n"
            f"{csv_text}"
        )

        # 3. Also include tail for large datasets
        if len(sheet_df) > max_sample_rows and len(sheet_df) > 20:
            tail_sample = sheet_df.tail(min(10, max_sample_rows // 10))
            tail_csv = tail_sample.to_csv(index=False)
            context_parts.append(
                f"\nLast {len(tail_sample)} rows from '{name}':\n{tail_csv}"
            )

    return "\n\n".join(context_parts)


# ── Load settings ───────────────────────────────────────────────
settings = get_settings()

# ── Page config ─────────────────────────────────────────────────
st.set_page_config(page_title="Excel Chat", page_icon="📈")

# ── Custom CSS ──────────────────────────────────────────────────
inject_chat_css()

# ── Session state ───────────────────────────────────────────────
init_api_key_state(settings)

if "excel_history" not in st.session_state:
    st.session_state.excel_history = []

# ── Header ──────────────────────────────────────────────────────
st.header("📈 Chat with Excel Data")

# ── Sidebar ─────────────────────────────────────────────────────
with st.sidebar:
    # API key is loaded automatically from .env via init_api_key_state()
    if st.session_state.api_key:
        st.success("🔑 API Key loaded from .env", icon="✅")
    else:
        st.warning("⚠️ No API key found. Add GOOGLE_API_KEY to your .env file.")

    st.markdown("---")

    max_sample_rows = st.slider(
        "Sample rows to include in prompt",
        min_value=50,
        max_value=5000,
        value=500,
        step=50,
        help=(
            "Number of sample rows sent to Gemini alongside the full "
            "statistical summary. More rows = better answers but higher token cost."
        ),
    )

    st.markdown("---")

    render_sidebar_history(
        "excel_history", "excel_chat",
        rerun_key="excel_rerun", reset_key="excel_reset",
    )

# ── Upload Excel ────────────────────────────────────────────────
uploaded_excel = st.file_uploader(
    "Upload an Excel file", type=["xlsx", "xls"]
)

if uploaded_excel is not None:
    try:
        # Read all sheets — use openpyxl for full accuracy
        raw_sheets = pd.read_excel(
            uploaded_excel,
            sheet_name=None,
            engine="openpyxl",
            dtype=str,  # Read everything as string first to preserve raw values
        )

        all_sheets = {}
        all_sheets_raw = {}  # Keep string versions for display
        for name, sheet_df in raw_sheets.items():
            cleaned = _clean_dataframe(sheet_df)
            if not cleaned.empty:
                all_sheets_raw[name] = cleaned.copy()
                # Now convert numeric columns properly
                for col in cleaned.columns:
                    cleaned[col] = pd.to_numeric(cleaned[col], errors="ignore")
                all_sheets[name] = cleaned
    except Exception as e:
        st.error(f"Failed to parse Excel file: {e}")
        st.stop()

    if not all_sheets:
        st.error("All sheets in this workbook are empty after cleanup.")
        st.stop()

    sheet_names = list(all_sheets.keys())

    # ── Sheet selector ──────────────────────────────────────────
    if len(sheet_names) > 1:
        selected_sheet = st.selectbox(
            "Select a sheet to preview and query",
            options=["All Sheets"] + sheet_names,
            index=0,
        )
    else:
        selected_sheet = sheet_names[0]

    # ── Metrics ─────────────────────────────────────────────────
    if selected_sheet == "All Sheets":
        total_rows = sum(len(df) for df in all_sheets.values())
        total_cols = sum(len(df.columns) for df in all_sheets.values())
        unique_cols = set()
        for df in all_sheets.values():
            unique_cols.update(df.columns)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Rows", f"{total_rows:,}")
        col2.metric("Sheets", len(sheet_names))
        col3.metric("Total Columns", f"{len(unique_cols)}")
        col4.metric("Size", f"{uploaded_excel.size / 1024:.1f} KB")
    else:
        df = all_sheets[selected_sheet]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Rows", f"{len(df):,}")
        col2.metric("Columns", len(df.columns))
        col3.metric("Non-null Cells", f"{df.notna().sum().sum():,}")
        col4.metric("Size", f"{uploaded_excel.size / 1024:.1f} KB")

    # ── Complete Data Preview ───────────────────────────────────
    st.subheader("📋 Complete Data Preview")

    if selected_sheet == "All Sheets":
        for name, sheet_df in all_sheets.items():
            with st.expander(
                f"📄 {name} — {len(sheet_df):,} rows × {len(sheet_df.columns)} cols",
                expanded=len(sheet_names) == 1,
            ):
                # Show column info
                st.caption(f"Columns: {', '.join(str(c) for c in sheet_df.columns)}")
                # Full dataframe with pagination via Streamlit's built-in scrolling
                st.dataframe(sheet_df, use_container_width=True, height=400)

                # Quick stats for numeric columns
                numeric_cols = sheet_df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    with st.expander("📊 Quick Statistics", expanded=False):
                        st.dataframe(
                            sheet_df[numeric_cols].describe().round(2),
                            use_container_width=True,
                        )
    else:
        # Show column info
        st.caption(f"Columns: {', '.join(str(c) for c in df.columns)}")
        # Full dataframe view
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
    for q, a, *_ in st.session_state.excel_history:
        render_chat_message(q, a)

    # ── Question ────────────────────────────────────────────────
    with st.form("excel_question_form", clear_on_submit=True):
        question = st.text_input("Ask a question about this data")
        submitted = st.form_submit_button("Ask", use_container_width=True)

    if submitted and question:
        if not st.session_state.api_key:
            st.warning("⚠️ No API key found. Add GOOGLE_API_KEY to your .env file.")
        else:
            # Build full context with statistical summary + sample data
            context = _build_full_context(
                all_sheets, selected_sheet, max_sample_rows
            )

            with st.spinner("Analysing data …"):
                try:
                    configure_gemini(st.session_state.api_key)
                    answer = ask_direct(
                        question=question,
                        context_text=context,
                        api_key=st.session_state.api_key,
                        prompt_template=EXCEL_PROMPT,
                    )
                except Exception as e:
                    logger.exception("Excel Gemini error")
                    st.error(f"Error: {e}")
                    st.stop()

            st.session_state.excel_history.append(
                (
                    question,
                    answer,
                    "Google Gemini",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    uploaded_excel.name,
                )
            )
            st.rerun()

else:
    st.info("👆 Upload an Excel file (.xlsx) to get started.")
