import asyncio
from collections.abc import Iterator

import anthropic
import httpx2
import pytest
from fastapi.testclient import TestClient

from app.booking.base import BookingUnavailableError
from app.main import create_app
from app.receptionist.claude import ClaudeReceptionist
from app.receptionist.intent import format_time
from tests.booking_fakes import (
    SATURDAY,
    ScriptedClaude,
    last_tool_result,
    message,
    mock_provider,
    now,
    text,
    tool_use,
)
from tests.conftest import make_settings
from tests.test_api import answer_text, parse_sse


def make_client(provider=None, llm=None, **settings) -> TestClient:
    app = create_app(
        make_settings(**settings),
        booking_providers={"kingsway": provider or mock_provider()},
        receptionist_llm=llm,
    )
    app.state.services.receptionist.now = now
    return TestClient(app)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with make_client() as c:
        yield c


def ask(client: TestClient, question: str, action: dict | None = None, session: str = "s1"):
    body: dict = {"question": question, "session_id": session}
    if action:
        body["action"] = action
    res = client.post("/bots/kingsway/ask", json=body)
    assert res.status_code == 200, res.text
    return parse_sse(res.text)


def of_type(events: list[dict], kind: str) -> list[dict]:
    return [e for e in events if e["type"] == kind]


def test_bot_config_says_it_can_book(client):
    body = client.get("/bots/kingsway").json()
    assert body["booking"] is True and body["mode"] == "demo"
    assert client.get("/bots/northwind").json()["booking"] is False


def test_full_booking_flow_over_sse(client):
    events = ask(client, "Is Saturday afternoon open for a skin fade?")
    assert [e["type"] for e in events] == ["meta", "text", "choices", "done"]
    assert events[-1]["handoff"] is False
    chips = of_type(events, "choices")[0]
    assert chips["kind"] == "slot" and chips["options"]

    first = chips["options"][0]
    events = ask(client, first["label"], {"type": "slot", "id": first["id"]})
    assert "name and email" in answer_text(events)

    events = ask(client, "Alex Chen, alex@example.com")
    pending = of_type(events, "booking")[0]
    assert pending["status"] == "pending" and pending["service"] == "Skin fade"
    assert first["label"] in pending["when"]

    events = ask(client, "Book it", {"type": "confirm"})
    confirmed = of_type(events, "booking")[0]
    assert confirmed["status"] == "confirmed" and confirmed["reference"].startswith("KC-")


def test_general_questions_still_answer_from_the_help_center(client):
    events = ask(client, "What's your cancellation policy?")
    assert of_type(events, "citation"), events
    assert "2 hours" in answer_text(events)
    assert not of_type(events, "choices")


def test_actions_are_validated(client):
    res = client.post(
        "/bots/kingsway/ask",
        json={"question": "x", "session_id": "s1", "action": {"type": "delete_all"}},
    )
    assert res.status_code == 422
    res = client.post(
        "/bots/kingsway/ask",
        json={"question": "x", "session_id": "s1", "action": {"type": "slot", "id": "<b>"}},
    )
    assert res.status_code == 422
    res = client.post(
        "/bots/northwind/ask",
        json={"question": "x", "session_id": "s1", "action": {"type": "confirm"}},
    )
    assert res.status_code == 400


def test_confirm_with_nothing_pending_books_nothing(client):
    events = ask(client, "yes", {"type": "confirm"})
    assert "nothing waiting" in answer_text(events)
    assert not of_type(events, "booking")


class DownProvider:
    def __init__(self) -> None:
        self.catalog = mock_provider().catalog

    async def find_slots(self, service_id, day):
        raise BookingUnavailableError("down")

    async def book(self, slot, customer, notes=""):
        raise BookingUnavailableError("down")


def test_booking_system_down_offers_the_phone_and_handoff():
    with make_client(provider=DownProvider()) as c:
        events = ask(c, "Book a fade on Saturday")
    assert "(416) 555-0187" in answer_text(events)
    assert events[-1]["type"] == "done" and events[-1]["handoff"] is True


def claude(script: ScriptedClaude) -> ClaudeReceptionist:
    client = anthropic.AsyncAnthropic(
        api_key="k",
        max_retries=0,
        http_client=anthropic.DefaultAsyncHttpxClient(
            transport=httpx2.MockTransport(script.handler)
        ),
    )
    return ClaudeReceptionist(client, model="claude-haiku-5-5")


def test_live_mode_uses_claude_tools_and_taps_skip_the_model():
    script = ScriptedClaude(
        [
            message(
                [
                    tool_use(
                        "check_availability",
                        {"service": "fade", "date": "2026-11-14", "time_of_day": "any"},
                    )
                ],
                stop_reason="tool_use",
            ),
            lambda body: message(
                [text(f"Yes, Saturday has {last_tool_result(body)['times'][0]['time']} open.")]
            ),
        ]
    )
    provider = mock_provider()
    with make_client(provider=provider, llm=claude(script)) as c:
        events = ask(c, "Any availability Saturday for a fade?")
        assert events[0] == {"type": "meta", "provider": "anthropic", "notice": None}
        chips = of_type(events, "choices")[0]["options"]
        assert answer_text(events) == f"Yes, Saturday has {chips[0]['label']} open."
        # A tap is handled without another model call.
        ask(c, chips[0]["label"], {"type": "slot", "id": chips[0]["id"]})
    assert len(script.bodies) == 2
    real = asyncio.run(provider.find_slots("kingsway_svc_fade", SATURDAY))
    assert {o["label"] for o in chips} <= {format_time(s.start) for s in real}


def test_live_mode_falls_back_to_offline_when_claude_fails():
    def fail(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(529, json={"type": "error", "error": {"type": "overloaded_error"}})

    client = anthropic.AsyncAnthropic(
        api_key="k",
        max_retries=0,
        http_client=anthropic.DefaultAsyncHttpxClient(transport=httpx2.MockTransport(fail)),
    )
    llm = ClaudeReceptionist(client, model="claude-haiku-5-5")
    with make_client(llm=llm) as c:
        events = ask(c, "Book a fade on Saturday")
    assert events[0]["provider"] == "mock" and events[0]["notice"]
    assert of_type(events, "choices")


def test_live_quota_exhausted_uses_offline_mode():
    script = ScriptedClaude([])
    with make_client(llm=claude(script), live_questions_per_day=1) as c:
        c.app.state.services.receptionist.quota.daily.take()
        events = ask(c, "Book a fade on Saturday")
    assert script.bodies == []
    assert events[0]["provider"] == "mock" and "daily limit" in events[0]["notice"]


async def test_mock_saturday_has_openings_for_the_demo():
    assert await mock_provider().find_slots("kingsway_svc_fade", SATURDAY)
