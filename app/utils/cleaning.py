"""
Text normalization pipeline.

Applied after parsing and before chunking to ensure clean, consistent text.
"""

import re
import unicodedata


def normalize_text(text: str) -> str:
    """
    Full normalization pipeline:
      1. Unicode NFKC normalization
      2. Remove control characters (keep newlines/tabs)
      3. Collapse excessive blank lines (max 2 newlines)
      4. Collapse horizontal whitespace
      5. Strip leading/trailing whitespace
    """
    if not text:
        return ""

    # 1. Unicode normalization
    text = unicodedata.normalize("NFKC", text)

    # 2. Remove control characters except \n, \r, \t
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # 3. Normalize line endings to \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 4. Collapse 3+ newlines into double newline (preserve paragraphs)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 5. Collapse horizontal whitespace (spaces/tabs) into single space
    text = re.sub(r"[ \t]{2,}", " ", text)

    # 6. Strip each line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()


def is_garbage(text: str, threshold: float = 0.5) -> bool:
    """
    Return True if the text appears to be garbage (encoding artifacts).

    Heuristic: if more than `threshold` fraction of characters are
    non-alphanumeric and non-whitespace, consider it garbage.
    """
    if not text:
        return True

    non_alnum = sum(1 for c in text if not c.isalnum() and not c.isspace())
    return (non_alnum / len(text)) > threshold
