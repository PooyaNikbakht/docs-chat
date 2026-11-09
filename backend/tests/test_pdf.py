import pytest

from app.errors import AppError
from app.ingest.pdf import extract_pdf, is_probably_scanned
from tests.conftest import make_pdf


def test_extracts_text_per_page():
    data = make_pdf(["First page has some words on it.", "Second page has other words."])
    out = extract_pdf(data, max_pages=10, min_chars_per_page=10)
    assert len(out.pages) == 2
    assert "Second page" in out.pages[1]


def test_rejects_non_pdf():
    with pytest.raises(AppError) as err:
        extract_pdf(b"hello", max_pages=10, min_chars_per_page=10)
    assert err.value.code == "invalid_file"


def test_rejects_damaged_pdf():
    with pytest.raises(AppError) as err:
        extract_pdf(b"%PDF-1.4 garbage", max_pages=10, min_chars_per_page=10)
    assert err.value.code == "invalid_pdf"


def test_rejects_too_many_pages():
    data = make_pdf(["page text"] * 4)
    with pytest.raises(AppError) as err:
        extract_pdf(data, max_pages=3, min_chars_per_page=1)
    assert err.value.code == "too_many_pages"
    assert err.value.status == 413


def test_detects_scanned_pdf():
    data = make_pdf(["", "", ""])  # pages with no text layer, like scans
    with pytest.raises(AppError) as err:
        extract_pdf(data, max_pages=10, min_chars_per_page=40)
    assert err.value.code == "scanned_pdf"


def test_scanned_heuristic():
    assert is_probably_scanned(["", "  ", "x"], 40)
    assert not is_probably_scanned(["word " * 20, ""], 40)
