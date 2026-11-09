import time
from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from app.bots import NORTHWIND
from app.main import create_app
from app.models import TextEvent
from tests.conftest import make_settings
from tests.test_api import answer_text, parse_sse, upload

PAUSE = "Can I pause my subscription?"
FRONTEND = "http://localhost:3010"


def ask_bot(client: TestClient, question: str, session: str = "s1", bot: str = "northwind"):
    res = client.post(f"/bots/{bot}/ask", json={"question": question, "session_id": session})
    return res, (parse_sse(res.text) if res.status_code == 200 else None)


class RecordingLive:
    """A live provider stand-in that records the persona and answers without citations."""

    name = "anthropic"

    def __init__(self) -> None:
        self.calls = 0
        self.personas: list = []

    async def stream_answer(self, question, chunks, history, persona=None) -> AsyncIterator:
        self.calls += 1
        self.personas.append(persona)
        yield TextEvent(text="An answer with no source.")


# ---- config ----


def test_bot_config_is_public_widget_config(client):
    res = client.get("/bots/northwind")
    assert res.status_code == 200
    body = res.json()
    assert body == {
        "id": "northwind",
        "name": NORTHWIND.name,
        "business": "Northwind Coffee Co.",
        "subline": "Answers from Northwind's help center",
        "greeting": NORTHWIND.greeting,
        "suggestions": list(NORTHWIND.suggestions),
        "accent_color": NORTHWIND.accent_color,
        "handoff_text": "Talk to a human",
        "handoff_url": "http://localhost:3010/contact",
        "tooltip": NORTHWIND.tooltip,
        "source_label": "Help center",
        "mode": "demo",
        "booking": False,
        "show_sources": False,
        "page_links": [
            {"page": page, "label": label, "url": f"http://localhost:3010{path}"}
            for page, label, path in NORTHWIND.page_links
        ],
    }


def test_handoff_url_follows_the_site_setting():
    with TestClient(create_app(make_settings(public_site_url="https://bot.example/"))) as c:
        assert c.get("/bots/northwind").json()["handoff_url"] == "https://bot.example/contact"


def test_live_provider_reports_live_mode():
    with TestClient(create_app(make_settings(), provider=RecordingLive())) as c:
        # The mode follows the configured provider, not the injected test double.
        assert c.get("/bots/northwind").json()["mode"] == "demo"
    settings = make_settings(llm_provider="anthropic", anthropic_api_key="x")
    with TestClient(create_app(settings, provider=RecordingLive())) as c:
        assert c.get("/bots/northwind").json()["mode"] == "live"


def test_unknown_bot_is_404(client):
    for res in (client.get("/bots/nope"), ask_bot(client, PAUSE, bot="nope")[0]):
        assert res.status_code == 404
        assert res.json()["error"] == {"code": "not_found", "message": "That bot doesn't exist."}


# ---- asking ----


def test_bot_answers_from_the_help_center_with_a_source(client):
    res, events = ask_bot(client, PAUSE)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/event-stream")
    assert events[0] == {"type": "meta", "provider": "mock", "notice": None}
    assert "pause your subscription for up to 3 months" in answer_text(events)
    cites = [e for e in events if e["type"] == "citation"]
    assert cites and all(c["page"] == 4 for c in cites)  # the subscriptions page
    assert events[-1]["grounded"] is True
    assert events[-1]["handoff"] is False


def test_off_topic_question_gets_not_covered_reply_with_handoff():
    live = RecordingLive()
    settings = make_settings(whole_document_max_words=0)
    with TestClient(create_app(settings, provider=live)) as c:
        _, events = ask_bot(c, "Do you sell laptops?")
    assert answer_text(events) == NORTHWIND.not_found
    assert events[-1] == {
        "type": "done",
        "provider": "anthropic",
        "grounded": False,
        "citations": 0,
        "handoff": True,
    }
    assert live.calls == 0, "nothing relevant was retrieved, so no model is called"


def test_answer_without_sources_offers_the_handoff():
    with TestClient(create_app(make_settings(), provider=RecordingLive())) as c:
        _, events = ask_bot(c, PAUSE)
    assert events[-1]["grounded"] is False
    assert events[-1]["handoff"] is True


def test_bot_speaks_as_the_business_and_uploads_use_the_document_persona(sample_bytes):
    live = RecordingLive()
    with TestClient(create_app(make_settings(), provider=live)) as c:
        ask_bot(c, PAUSE)
        doc_id = upload(c, sample_bytes).json()["id"]
        c.post(f"/documents/{doc_id}/ask", json={"question": PAUSE, "session_id": "s"})
    bot_persona, doc_persona = live.personas
    assert "Northwind Coffee Co.'s website" in bot_persona.system_prompt
    assert NORTHWIND.not_found in bot_persona.system_prompt
    assert "Answer only from the passages" in bot_persona.system_prompt
    assert "Northwind" not in doc_persona.system_prompt
    assert "one of the business's documents" in doc_persona.system_prompt


def test_bot_follow_up_uses_its_own_session(client):
    ask_bot(client, PAUSE, session="visitor")
    _, events = ask_bot(client, "How do I cancel it?", session="visitor")
    assert "Cancel any time from your account" in answer_text(events)


def test_bot_questions_share_the_rate_limit():
    with TestClient(create_app(make_settings(ask_rate_limit_per_minute=1))) as c:
        assert ask_bot(c, PAUSE)[0].status_code == 200
        res, _ = ask_bot(c, PAUSE)
        assert res.status_code == 429
        assert res.json()["error"]["code"] == "rate_limited"


def test_bot_knowledge_base_is_pinned_and_never_expires(sample_bytes):
    settings = make_settings(document_ttl_seconds=60, max_pages=3)
    app = create_app(settings)
    with TestClient(app) as c:
        # Upload limits don't apply to the bot's own 9-page help center.
        assert upload(c, sample_bytes).json()["error"]["code"] == "too_many_pages"
        services = app.state.services
        services.documents.max_items = 0  # even a full store can't evict it
        services.documents.clock = lambda: time.time() + 7200
        res, events = ask_bot(c, PAUSE)
        assert res.status_code == 200
        assert events[-1]["grounded"] is True


def test_uploaded_documents_still_expire(sample_bytes):
    app = create_app(make_settings(document_ttl_seconds=60))
    with TestClient(app) as c:
        doc_id = upload(c, sample_bytes).json()["id"]
        app.state.services.documents.clock = lambda: time.time() + 7200
        assert c.get(f"/documents/{doc_id}").status_code == 404


# ---- CORS per route ----


def preflight(client: TestClient, path: str, origin: str):
    return client.options(
        path,
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )


def test_bot_routes_allow_any_origin_for_the_demo_bot(client):
    site = "https://some-shop.example"
    assert preflight(client, "/bots/northwind/ask", site).status_code == 200
    assert preflight(client, "/bots/northwind/ask", site).headers["access-control-allow-origin"]
    res = client.get("/bots/northwind", headers={"Origin": site})
    assert res.headers["access-control-allow-origin"] == "*"
    res = client.post(
        "/bots/northwind/ask",
        json={"question": PAUSE, "session_id": "x"},
        headers={"Origin": site},
    )
    assert res.headers["access-control-allow-origin"] == "*"


def test_upload_and_document_routes_allow_only_the_frontend(client):
    evil = "https://evil.example"
    assert preflight(client, "/documents", evil).status_code == 400
    assert "access-control-allow-origin" not in preflight(client, "/documents", evil).headers
    ok = preflight(client, "/documents", FRONTEND)
    assert ok.headers["access-control-allow-origin"] == FRONTEND
    assert (
        "access-control-allow-origin" not in client.get("/health", headers={"Origin": evil}).headers
    )
    # Unknown bots fall back to the strict policy.
    assert (
        "access-control-allow-origin"
        not in client.get("/bots/nope", headers={"Origin": evil}).headers
    )


def test_bot_origins_come_from_bot_config():
    from dataclasses import replace

    locked = replace(NORTHWIND, allowed_origins=("https://northwind.example",))
    with TestClient(create_app(make_settings(), bots={"northwind": locked})) as c:
        ok = c.get("/bots/northwind", headers={"Origin": "https://northwind.example"})
        assert ok.headers["access-control-allow-origin"] == "https://northwind.example"
        other = c.get("/bots/northwind", headers={"Origin": "https://other.example"})
        assert "access-control-allow-origin" not in other.headers


# ---- questions about the assistant itself ----


def test_about_questions_get_the_bots_own_answer_without_a_model(sample_bytes):
    live = RecordingLive()
    app = create_app(make_settings(llm_provider="anthropic", anthropic_api_key="x"), provider=live)
    with TestClient(app) as client:
        questions = ("What can you help me with?", "what can I ask?", "Who are you?", "help")
        for i, question in enumerate(questions):
            _, events = ask_bot(client, question, session=f"about-{i}")
            assert answer_text(events) == NORTHWIND.about
            assert events[-1]["handoff"] is False
    assert live.calls == 0


def test_business_questions_still_go_to_retrieval(client):
    _, events = ask_bot(client, PAUSE)
    assert answer_text(events) != NORTHWIND.about


# ---- how strict the relevance check is ----

WEAK = "how much and how kinds are your coffees?"  # shares only "coffee" with the help center


def test_a_live_model_sees_weak_matches_and_decides_itself():
    live = RecordingLive()
    settings = make_settings(llm_provider="anthropic", anthropic_api_key="x")
    with TestClient(create_app(settings, provider=live)) as client:
        _, events = ask_bot(client, WEAK)
    assert live.calls == 1
    assert answer_text(events) == "An answer with no source."


def test_off_topic_questions_never_reach_the_model_for_long_documents():
    live = RecordingLive()
    settings = make_settings(
        llm_provider="anthropic", anthropic_api_key="x", whole_document_max_words=10
    )
    with TestClient(create_app(settings, provider=live)) as client:
        _, events = ask_bot(client, "What is the capital of France?")
    assert live.calls == 0
    assert answer_text(events) == NORTHWIND.not_found


def test_a_short_help_center_goes_to_the_model_whole_when_keywords_miss():
    live = RecordingLive()
    settings = make_settings(llm_provider="anthropic", anthropic_api_key="x")
    with TestClient(create_app(settings, provider=live)) as client:
        _, events = ask_bot(client, "What products do you have?")
    assert live.calls == 1
    assert answer_text(events) == "An answer with no source."


def test_demo_mode_still_needs_a_clear_match(client):
    _, events = ask_bot(client, WEAK)
    assert answer_text(events) == NORTHWIND.not_found


def test_weak_match_after_the_daily_cap_is_not_found_not_a_guess():
    live = RecordingLive()
    settings = make_settings(
        llm_provider="anthropic", anthropic_api_key="x", live_questions_per_day=1
    )
    with TestClient(create_app(settings, provider=live)) as client:
        ask_bot(client, PAUSE, session="cap-1")
        _, events = ask_bot(client, WEAK, session="cap-2")
    assert live.calls == 1
    assert answer_text(events) == NORTHWIND.not_found
