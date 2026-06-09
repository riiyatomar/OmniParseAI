"""
PDF parser with text extraction + OCR fallback for scanned pages.
"""

import logging

from PyPDF2 import PdfReader

from app.core.config import get_settings
from app.core.exceptions import FileParsingError
from app.parsers.base import BaseParser, ParsedDocument

logger = logging.getLogger(__name__)


class PdfParser(BaseParser):
    """
    Extract text from PDF files.

    Strategy:
      1. Try pypdf text extraction for each page.
      2. If a page yields < 50 characters, fall back to OCR
         (pdf2image + tesseract).
      3. Collect metadata (page count, author if available).
    """

    MIN_CHARS_PER_PAGE = 50  # below this, assume scanned page

    def parse(self, file_path: str) -> ParsedDocument:
        try:
            reader = PdfReader(file_path)
        except Exception as exc:
            raise FileParsingError(
                f"Cannot open PDF: {exc}"
            ) from exc

        pages_text: list[str] = []
        ocr_pages: list[int] = []

        for page_num, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()

            if len(text) < self.MIN_CHARS_PER_PAGE:
                # Attempt OCR fallback
                ocr_text = self._ocr_page(file_path, page_num)
                if ocr_text:
                    pages_text.append(ocr_text)
                    ocr_pages.append(page_num)
                else:
                    pages_text.append(text)  # keep whatever we got
            else:
                pages_text.append(text)

        full_text = "\n\n".join(pages_text)

        # Metadata
        info = reader.metadata or {}
        metadata = {
            "pages": len(reader.pages),
            "ocr_pages": ocr_pages,
            "author": getattr(info, "author", None) or "",
            "title": getattr(info, "title", None) or "",
        }

        if ocr_pages:
            logger.info(
                "OCR was used for pages: %s", ocr_pages
            )

        return ParsedDocument(
            text=full_text,
            pages_text=pages_text,
            metadata=metadata,
            doc_type="pdf",
            is_structured=False,
        )

    # ── OCR fallback ────────────────────────────────────────────

    def _ocr_page(self, pdf_path: str, page_num: int) -> str:
        """Convert a single PDF page to image and run tesseract."""
        settings = get_settings()
        try:
            from pdf2image import convert_from_path
            import pytesseract

            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

            poppler_kwargs = {}
            if settings.poppler_path:
                poppler_kwargs["poppler_path"] = settings.poppler_path

            images = convert_from_path(
                pdf_path,
                first_page=page_num,
                last_page=page_num,
                **poppler_kwargs,
            )

            if images:
                text = pytesseract.image_to_string(images[0])
                return text.strip()

        except ImportError:
            logger.warning(
                "pdf2image or pytesseract not installed — skipping OCR for page %d",
                page_num,
            )
        except Exception as exc:
            logger.warning(
                "OCR failed for page %d: %s", page_num, exc
            )

        return ""
