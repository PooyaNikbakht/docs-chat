import json
from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.models import TextEvent
from app.providers.base import NOT_IN_DOC_MESSAGE, ProviderError
from tests.conftest import make_pdf, make_settings

PAUSE = "Can I pause my subscription?"


def parse_sse(body: str) -> list[dict]:
    events = []
    for block in body.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines() if ": " in line)
        data = json.loads(lines["data"])
        assert data["type"] == lines["event"]
        events.append(data)
    return events


def upload(client: TestClient, data: bytes, name: str = "doc.pdf", ctype: str = "application/pdf"):
    return client.post("/documents", files={"file": (name, data, ctype)})


def ask(client: TestClient, doc_id: str, question: str, session: str = "s1"):
    res = client.post(
        f"/documents/{doc_id}/ask", json={"question": question, "session_id": session}
    )
    return res, (parse_sse(res.text) if res.status_code == 200 else None)


def answer_text(events: list[dict]) -> str:
    return "".join(e["text"] for e in events if e["type"] == "text")


# ---- health and docs ----


def test_health_reports_mock_provider(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["provider"] == "mock"
    assert body["limits"] == {"max_upload_mb": 20, "max_pages": 300, "document_ttl_minutes": None}


def test_openapi_docs_are_served(client):
    assert client.get("/docs").status_code == 200
    assert "/documents/{doc_id}/ask" in client.get("/openapi.json").json()["paths"]


def test_cors_allows_only_the_frontend_origin(client):
    ok = client.options(
        "/health",
        headers={"Origin": "http://localhost:3010", "Access-Control-Request-Method": "GET"},
    )
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:3010"
    bad = client.get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in bad.headers


# ---- documents ----


def test_upload_and_get_document(client, sample_bytes):
    res = upload(client, sample_bytes, "northwind-help-center.pdf")
    assert res.status_code == 201
    doc = res.json()
    assert doc["name"] == "northwind-help-center.pdf"
    assert doc["pages"] == 9
    assert doc["chunks"] >= 1
    assert client.get(f"/documents/{doc['id']}").json() == doc


def test_sample_endpoint(client):
    res = client.post("/documents/sample")
    assert res.status_code == 201
    assert res.json()["pages"] == 9
    assert PAUSE in res.json()["suggestions"]


def test_uploads_get_suggestions_from_headings(client, sample_bytes):
    doc = upload(client, sample_bytes).json()
    assert len(doc["suggestions"]) == 3
    assert all(q.startswith("What does it say about") for q in doc["suggestions"])


def test_unknown_document_is_404(client):
    res = client.get("/documents/nope")
    assert res.status_code == 404
    assert res.json() == {
        "error": {"code": "not_found", "message": "That document doesn't exist or has expired."}
    }


@pytest.mark.parametrize(
    ("data", "name", "ctype", "status", "code"),
    [
        (b"not a pdf", "notes.txt", "text/plain", 415, "invalid_file"),
        (b"not a pdf", "fake.pdf", "application/pdf", 415, "invalid_file"),
        (b"", "empty.pdf", "application/pdf", 422, "invalid_file"),
    ],
)
def test_upload_rejects_bad_files(client, data, name, ctype, status, code):
    res = upload(client, data, name, ctype)
    assert res.status_code == status
    assert res.json()["error"]["code"] == code


def test_upload_rejects_scanned_pdf(client):
    res = upload(client, make_pdf(["", ""]))
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "scanned_pdf"
    assert "scanned" in res.json()["error"]["message"].lower()


def test_upload_limits_follow_settings(sample_bytes):
    settings = make_settings(max_pages=3)
    with TestClient(create_app(settings)) as c:
        res = upload(c, sample_bytes)
        assert res.status_code == 413
        assert res.json()["error"]["code"] == "too_many_pages"
    with TestClient(create_app(make_settings(max_upload_mb=0))) as c:
        res = upload(c, sample_bytes)
        assert res.status_code == 413
        assert res.json()["error"]["code"] == "file_too_large"


def test_public_demo_preset_tightens_limits():
    s = make_settings(public_demo=True)
    assert (s.max_upload_mb, s.max_pages) == (5, 25)
    assert (s.live_questions_per_ip_per_hour, s.live_questions_per_day) == (10, 300)
    assert s.document_ttl_seconds == 3600
    # An explicit value still wins over the preset.
    assert make_settings(public_demo=True, max_pages=40).max_pages == 40


# ---- ask ----


def test_ask_streams_cited_answer_then_not_in_document(client, sample_bytes):
    doc_id = upload(client, sample_bytes).json()["id"]

    res, events = ask(client, doc_id, PAUSE)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/event-stream")
    assert events[0] == {"type": "meta", "provider": "mock", "notice": None}
    assert events[-1]["type"] == "done"
    assert events[-1]["grounded"] is True
    assert "3 months" in answer_text(events)
    cites = [e for e in events if e["type"] == "citation"]
    assert cites and cites[0]["page"] == 4
    assert set(cites[0]) == {"type", "index", "chunk_id", "page", "quote", "context"}

    _, off = ask(client, doc_id, "What is the capital of France?")
    assert answer_text(off) == NOT_IN_DOC_MESSAGE
    assert off[-1] == {
        "type": "done",
        "provider": "mock",
        "grounded": False,
        "citations": 0,
        "handoff": True,
    }


def test_follow_up_uses_session_history(client, sample_bytes):
    doc_id = upload(client, sample_bytes).json()["id"]
    ask(client, doc_id, PAUSE, session="a")
    _, events = ask(client, doc_id, "How do I cancel it?", session="a")
    assert "Cancel any time from your account" in answer_text(events)


def test_ask_unknown_document(client):
    res, _ = ask(client, "missing", PAUSE)
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "not_found"


@pytest.mark.parametrize(
    "body", [{"question": "", "session_id": "s"}, {"question": "hi", "session_id": "bad id!"}, {}]
)
def test_ask_validation_errors_are_structured(client, sample_bytes, body):
    doc_id = upload(client, sample_bytes).json()["id"]
    res = client.post(f"/documents/{doc_id}/ask", json=body)
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "validation_error"


def test_ask_is_rate_limited_per_ip(sample_bytes):
    with TestClient(create_app(make_settings(ask_rate_limit_per_minute=2))) as c:
        doc_id = upload(c, sample_bytes).json()["id"]
        assert ask(c, doc_id, PAUSE)[0].status_code == 200
        assert ask(c, doc_id, PAUSE)[0].status_code == 200
        res, _ = ask(c, doc_id, PAUSE)
        assert res.status_code == 429
        assert res.json()["error"]["code"] == "rate_limited"


# ---- provider fallback ----


class FakeLive:
    """A live provider stand-in that either answers or fails."""

    name = "anthropic"

    def __init__(self, fail: ProviderError | None = None, fail_after_text: bool = False) -> None:
        self.fail = fail
        self.fail_after_text = fail_after_text
        self.calls = 0

    async def stream_answer(
        self, question, chunks, history, persona=None
    ) -> AsyncIterator[TextEvent]:
        self.calls += 1
        self.persona = persona
        if self.fail and self.fail_after_text:
            yield TextEvent(text="Partial ")
        if self.fail:
            raise self.fail
        yield TextEvent(text="Live answer.")


def test_provider_error_falls_back_to_mock(sample_bytes):
    live = FakeLive(fail=ProviderError("provider_error", "Credit balance is too low."))
    with TestClient(create_app(make_settings(), provider=live)) as c:
        doc_id = upload(c, sample_bytes).json()["id"]
        _, events = ask(c, doc_id, PAUSE)
    assert events[0]["provider"] == "mock"
    assert "demo mode" in events[0]["notice"]
    assert events[-1]["type"] == "done" and events[-1]["provider"] == "mock"
    assert "3 months" in answer_text(events)


def test_refusal_is_reported_not_hidden(sample_bytes):
    live = FakeLive(fail=ProviderError("refused", "Declined.", fallback_ok=False))
    with TestClient(create_app(make_settings(), provider=live)) as c:
        doc_id = upload(c, sample_bytes).json()["id"]
        _, events = ask(c, doc_id, PAUSE)
    assert events[0]["provider"] == "anthropic"
    assert events[-1] == {"type": "error", "code": "refused", "message": "Declined."}


def test_mid_stream_failure_sends_error_event(sample_bytes):
    live = FakeLive(fail=ProviderError("provider_unavailable", "Lost it."), fail_after_text=True)
    with TestClient(create_app(make_settings(), provider=live)) as c:
        doc_id = upload(c, sample_bytes).json()["id"]
        _, events = ask(c, doc_id, PAUSE)
    assert [e["type"] for e in events] == ["meta", "text", "error"]


def test_live_caps_switch_to_mock(sample_bytes):
    live = FakeLive()
    settings = make_settings(live_questions_per_ip_per_hour=1)
    with TestClient(create_app(settings, provider=live)) as c:
        doc_id = upload(c, sample_bytes).json()["id"]
        _, first = ask(c, doc_id, PAUSE)
        _, second = ask(c, doc_id, PAUSE)
    assert first[0]["provider"] == "anthropic" and answer_text(first) == "Live answer."
    assert second[0]["provider"] == "mock" and "hourly limit" in second[0]["notice"]
    assert live.calls == 1


def test_daily_cap_switches_to_mock(sample_bytes):
    live = FakeLive()
    with TestClient(create_app(make_settings(live_questions_per_day=1), provider=live)) as c:
        doc_id = upload(c, sample_bytes).json()["id"]
        ask(c, doc_id, PAUSE, session="x")
        _, events = ask(c, doc_id, PAUSE, session="y")
    assert events[0]["provider"] == "mock" and "daily limit" in events[0]["notice"]


def test_unanswerable_questions_never_call_the_model(sample_bytes):
    # Short documents can go to the model whole (see test_bots); this checks the gate itself.
    live = FakeLive()
    with TestClient(create_app(make_settings(whole_document_max_words=0), provider=live)) as c:
        doc_id = upload(c, sample_bytes).json()["id"]
        _, events = ask(c, doc_id, "What is the capital of France?")
    assert live.calls == 0
    assert answer_text(events) == NOT_IN_DOC_MESSAGE
