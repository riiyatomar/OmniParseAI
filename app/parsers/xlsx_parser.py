"""
Excel (.xlsx) parser — converts structured rows to natural-language text for embedding.

Each sheet in the workbook is parsed independently.  Rows are converted to
descriptive sentences (same format as CsvParser) so the embedding model
captures the semantics.  Each row is prefixed with its sheet name.

Handles real-world Excel files with:
  - Empty rows/columns (dropped automatically)
  - "Unnamed" columns from merged or blank header cells
  - Multiple header rows (auto-detected)
"""

import logging
import re
from typing import Dict, List

import pandas as pd

from app.core.exceptions import FileParsingError
from app.parsers.base import BaseParser, ParsedDocument

logger = logging.getLogger(__name__)

# Regex to match pandas auto-generated "Unnamed: X" column names
_UNNAMED_RE = re.compile(r"^Unnamed:\s*\d+$")


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean a raw DataFrame read from Excel:
      1. Drop rows that are entirely empty / NaN.
      2. Drop columns that are entirely empty / NaN.
      3. Drop "Unnamed: X" columns that have ≤10% non-null values
         (likely artefacts from merged cells or blank header columns).
      4. Strip whitespace from string cells.
    """
    # Drop completely empty rows and columns
    df = df.dropna(how="all")           # rows where every cell is NaN
    df = df.dropna(axis=1, how="all")   # columns where every cell is NaN

    if df.empty:
        return df

    # Drop "Unnamed" columns that are mostly empty (≤10% filled)
    cols_to_drop = []
    for col in df.columns:
        col_str = str(col)
        if _UNNAMED_RE.match(col_str):
            fill_ratio = df[col].notna().mean()
            if fill_ratio <= 0.10:
                cols_to_drop.append(col)
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
        logger.info("Dropped %d mostly-empty Unnamed columns", len(cols_to_drop))

    # Strip whitespace from string columns
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip().replace("nan", pd.NA)

    # Drop rows that became fully empty after cleanup
    df = df.dropna(how="all")

    # Reset index for clean iteration
    df = df.reset_index(drop=True)

    return df


def _detect_header_row(file_path: str, sheet_name: str, engine: str = "openpyxl") -> int:
    """
    Try to detect the actual header row by scanning the first 20 rows.
    Returns the row index (0-based) where headers likely start.

    Heuristic: the first row where ≥50% of cells are non-null strings
    (not numeric) is likely the header row.
    """
    try:
        sample = pd.read_excel(
            file_path, sheet_name=sheet_name, header=None,
            nrows=20, engine=engine,
        )
    except Exception:
        return 0

    for idx, row in sample.iterrows():
        non_null = row.dropna()
        if len(non_null) == 0:
            continue
        # Check if most non-null values are string-like (headers)
        str_count = sum(1 for v in non_null if isinstance(v, str))
        if len(non_null) >= 2 and str_count / len(non_null) >= 0.5:
            return int(idx)

    return 0


class XlsxParser(BaseParser):
    """
    Parse Excel (.xlsx) files into structured row-level text.

    Output:
      - ``rows_as_text``: each row as "[Sheet: Name] col1: val1, col2: val2, ..."
      - ``metadata``: per-sheet column names, dtypes, row counts, aggregate stats
      - ``is_structured = True``  → chunking will use row-based grouping
    """

    def parse(self, file_path: str) -> ParsedDocument:
        try:
            # First, get sheet names
            xls = pd.ExcelFile(file_path, engine="openpyxl")
            sheet_names = xls.sheet_names
        except Exception as exc:
            raise FileParsingError(
                f"Cannot read Excel file: {exc}"
            ) from exc

        if not sheet_names:
            raise FileParsingError("Excel file contains no sheets.")

        all_rows_as_text: List[str] = []
        sheets_meta: List[Dict] = []
        total_rows = 0
        total_cols = 0

        for sheet_name in sheet_names:
            try:
                # Detect the actual header row
                header_row = _detect_header_row(file_path, sheet_name)
                if header_row > 0:
                    logger.info(
                        "Sheet '%s': detected header at row %d",
                        sheet_name, header_row,
                    )

                df = pd.read_excel(
                    file_path,
                    sheet_name=sheet_name,
                    header=header_row,
                    engine="openpyxl",
                )
            except Exception as exc:
                logger.warning(
                    "Failed to read sheet '%s': %s", sheet_name, exc
                )
                continue

            # Clean the dataframe
            df = _clean_dataframe(df)

            if df.empty:
                logger.info("Skipping empty sheet '%s' (after cleanup)", sheet_name)
                continue

            # ── Schema description for this sheet ────────────────
            schema_parts: List[str] = []
            for col in df.columns:
                dtype = str(df[col].dtype)
                schema_parts.append(f"{col} ({dtype})")
            schema_description = ", ".join(schema_parts)

            # ── Row-to-text conversion ───────────────────────────
            for _, row in df.iterrows():
                # Skip rows where most values are NaN
                non_null = row.dropna()
                if len(non_null) < max(1, len(df.columns) * 0.2):
                    continue
                parts = [
                    f"{col}: {val}"
                    for col, val in row.items()
                    if pd.notna(val) and str(val).strip()
                ]
                if parts:
                    all_rows_as_text.append(
                        f"[Sheet: {sheet_name}] " + ", ".join(parts)
                    )

            # ── Per-sheet metadata ───────────────────────────────
            sheets_meta.append({
                "sheet_name": sheet_name,
                "rows": len(df),
                "columns": list(df.columns),
                "schema": schema_description,
                "dtypes": {col: str(df[col].dtype) for col in df.columns},
            })

            total_rows += len(df)
            total_cols = max(total_cols, len(df.columns))

        if not all_rows_as_text:
            raise FileParsingError(
                "Excel file has no data — all sheets are empty."
            )

        # ── Build a summary text for quick reference ─────────────
        sheet_name_list = [m["sheet_name"] for m in sheets_meta]
        summary = (
            f"Excel workbook with {len(sheets_meta)} sheet(s): "
            f"{', '.join(sheet_name_list)}.\n"
            f"Total: {total_rows} rows.\n\n"
            f"Sample data (first 5 rows):\n"
        )
        for line in all_rows_as_text[:5]:
            summary += f"  {line}\n"

        # ── Aggregate schema (combine all sheets) ────────────────
        all_schemas = "; ".join(
            f"[{m['sheet_name']}] {m['schema']}" for m in sheets_meta
        )

        metadata = {
            "total_rows": total_rows,
            "sheet_count": len(sheets_meta),
            "sheet_names": sheet_name_list,
            "sheets": sheets_meta,
            "schema": all_schemas,
        }

        logger.info(
            "Parsed Excel: %d sheet(s), %d total rows",
            len(sheets_meta), total_rows,
        )

        return ParsedDocument(
            text=summary,
            rows_as_text=all_rows_as_text,
            metadata=metadata,
            doc_type="xlsx",
            is_structured=True,
        )
