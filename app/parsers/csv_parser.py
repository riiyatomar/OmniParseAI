"""
CSV parser — converts structured rows to natural-language text for embedding.

Instead of treating a CSV as a blob of text, each row is converted to
a descriptive sentence so the embedding model captures the semantics.
"""

import logging
from typing import List

import pandas as pd

from app.core.exceptions import FileParsingError
from app.parsers.base import BaseParser, ParsedDocument

logger = logging.getLogger(__name__)


class CsvParser(BaseParser):
    """
    Parse CSV files into structured row-level text.

    Output:
      - ``rows_as_text``: each row as "col1: val1, col2: val2, ..."
      - ``metadata``: column names, dtypes, row count
      - ``is_structured = True`` → chunking will use row-based grouping
    """

    def parse(self, file_path: str) -> ParsedDocument:
        try:
            df = pd.read_csv(file_path)
        except Exception as exc:
            raise FileParsingError(
                f"Cannot read CSV file: {exc}"
            ) from exc

        if df.empty:
            raise FileParsingError("CSV file is empty — no rows found.")

        # ── Schema description ──────────────────────────────────
        schema_parts: List[str] = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            schema_parts.append(f"{col} ({dtype})")
        schema_description = ", ".join(schema_parts)

        # ── Row-to-text conversion ──────────────────────────────
        rows_as_text: List[str] = []
        for _, row in df.iterrows():
            parts = [f"{col}: {val}" for col, val in row.items()]
            rows_as_text.append(", ".join(parts))

        # ── Also build a summary text for quick reference ───────
        summary = (
            f"CSV with {len(df)} rows and {len(df.columns)} columns.\n"
            f"Columns: {schema_description}\n\n"
            f"Sample data (first 5 rows):\n"
        )
        for line in rows_as_text[:5]:
            summary += f"  {line}\n"

        metadata = {
            "rows": len(df),
            "columns": list(df.columns),
            "schema": schema_description,
            "dtypes": {col: str(df[col].dtype) for col in df.columns},
        }

        logger.info(
            "Parsed CSV: %d rows, %d columns", len(df), len(df.columns)
        )

        return ParsedDocument(
            text=summary,
            rows_as_text=rows_as_text,
            metadata=metadata,
            doc_type="csv",
            is_structured=True,
        )
