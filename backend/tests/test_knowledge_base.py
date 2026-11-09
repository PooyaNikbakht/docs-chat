"""The help center PDF and the sample website both come from one fact sheet."""

import json
from pathlib import Path

import pytest

from app.ingest.pdf import extract_pdf
from sample.generate_kb import (
    JSON_OUT,
    PDF_OUT,
    build_pdf,
    help_center_pages,
    load_facts,
    parse_facts,
    site_data,
)


@pytest.fixture(scope="module")
def facts():
    return load_facts()


def pdf_text(path: Path) -> list[str]:
    return extract_pdf(path.read_bytes(), max_pages=50, min_chars_per_page=10).pages


def test_parser_reads_bullets_and_tables():
    text = (
        "## Shop\n\n- name: Test\n- city: Here\n\n"
        "| a | b |\n|---|---|\n| 1 | 2 |\n\n## Cafés\n- x: y\n"
    )
    assert parse_facts(text) == {
        "shop": {"name": "Test", "city": "Here", "rows": [{"a": "1", "b": "2"}]},
        "cafes": {"x": "y"},
    }


def test_help_center_covers_the_prd_topics(facts):
    titles = [title for title, _ in help_center_pages(facts)]
    assert titles == [
        "Welcome to our help center",
        "Ordering and shipping",
        "Returns and refunds",
        "Subscriptions",
        "Our coffees",
        "Brewing guides",
        "Gift cards and wholesale",
        "Cafés, hours and contact",
    ]


def test_committed_pdf_matches_the_fact_sheet(facts, tmp_path):
    fresh = build_pdf(facts, tmp_path / "kb.pdf")
    assert pdf_text(fresh) == pdf_text(PDF_OUT), "run `make kb` to regenerate the PDF"


def test_committed_site_data_matches_the_fact_sheet(facts):
    if not JSON_OUT.exists():
        pytest.skip("frontend not checked out next to the backend")
    on_disk = json.loads(JSON_OUT.read_text(encoding="utf-8"))
    assert on_disk == site_data(facts), "run `make kb` to regenerate northwind.json"


def test_site_facts_appear_in_the_pdf(facts):
    text = " ".join(" ".join(p.split()) for p in pdf_text(PDF_OUT))
    data = site_data(facts)
    for coffee in data["coffees"]:
        assert f"A 340 g bag of {coffee['name']} costs ${coffee['price']}." in text
    assert f"free on orders over ${data['shipping']['free_canada_over']} in Canada" in text
    assert f"save {data['subscriptions']['discount_percent']} percent" in text
    for cafe in data["cafes"]:
        assert cafe["address"] in text
    assert "fictional business" in text
