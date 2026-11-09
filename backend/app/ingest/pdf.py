"""PDF text extraction with pypdf, plus validation of size, page count and scanned files."""

import io
import logging
from dataclasses import dataclass

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.errors import AppError

logger = logging.getLogger(__name__)

PDF_MAGIC = b"%PDF-"


@dataclass(frozen=True)
class ExtractedPdf:
    pages: list[str]  # text per page, index 0 is page 1


def extract_pdf(data: bytes, *, max_pages: int, min_chars_per_page: int) -> ExtractedPdf:
    """Extract text page by page. Raises AppError for anything we can't index."""
    if not data.startswith(PDF_MAGIC):
        raise AppError(415, "invalid_file", "That file isn't a PDF.")
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise AppError(422, "encrypted_pdf", "Password-protected PDFs aren't supported.")
        page_count = len(reader.pages)
    except PdfReadError as exc:
        raise AppError(422, "invalid_pdf", "We couldn't read that PDF. It may be damaged.") from exc

    if page_count == 0:
        raise AppError(422, "empty_pdf", "That PDF has no pages.")
    if page_count > max_pages:
        raise AppError(
            413,
            "too_many_pages",
            f"That PDF has {page_count} pages. The limit is {max_pages}.",
        )

    pages: list[str] = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:  # pypdf raises a range of errors on odd pages
            logger.warning("Failed to extract a page; treating it as empty", exc_info=True)
            pages.append("")

    if is_probably_scanned(pages, min_chars_per_page):
        raise AppError(
            422,
            "scanned_pdf",
            "This looks like a scanned PDF. Scanned PDFs aren't supported yet.",
        )
    return ExtractedPdf(pages=pages)


def is_probably_scanned(pages: list[str], min_chars_per_page: int) -> bool:
    """Very low text density means the pages are images, not text."""
    total = sum(len(p.strip()) for p in pages)
    return total < max(1, len(pages)) * min_chars_per_page
