from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fpdf import FPDF

from app.ingest.service import ingest_pdf
from app.models import Document
from app.settings import Settings

SAMPLE = Path(__file__).resolve().parents[1] / "sample" / "northwind-help-center.pdf"


def make_settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "llm_provider": "mock",
        "anthropic_api_key": "",
        "openai_api_key": "",
        "mock_delay_seconds": 0.0,
        "_env_file": None,
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def make_pdf(pages: list[str]) -> bytes:
    pdf = FPDF()
    pdf.set_font("Helvetica", size=11)
    for text in pages:
        pdf.add_page()
        if text:
            pdf.multi_cell(0, 6, text)
    return bytes(pdf.output())


@pytest.fixture
def sample_bytes() -> bytes:
    return SAMPLE.read_bytes()


@pytest.fixture
def sample_doc(sample_bytes: bytes) -> Document:
    return ingest_pdf("northwind-help-center.pdf", sample_bytes, make_settings())


@pytest.fixture
def client() -> Iterator[TestClient]:
    from app.main import create_app

    with TestClient(create_app(make_settings())) as c:
        yield c
