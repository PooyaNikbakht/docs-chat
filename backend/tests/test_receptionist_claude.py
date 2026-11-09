import anthropic
import httpx2
import pytest

from app.models import BookingEvent, ChoicesEvent, TextEvent
from app.providers.anthropic import FALLBACK_BETA
from app.providers.base import ProviderError
from app.receptionist.claude import ClaudeReceptionist
from app.receptionist.desk import BookingDesk, DeskState
from app.receptionist.intent import times_in
from tests.booking_fakes import (
    ScriptedClaude,
    last_tool_result,
    message,
    mock_provider,
    now,
    text,
    thinking,
    tool_use,
)

SYSTEM = "system prompt"


def receptionist(script: ScriptedClaude, model: str = "claude-haiku-5-5") -> ClaudeReceptionist:
    client = anthropic.AsyncAnthropic(
        api_key="test-key",
        max_retries=0,
        http_client=anthropic.DefaultAsyncHttpxClient(
            transport=httpx2.MockTransport(script.handler)
        ),
    )
    return ClaudeReceptionist(client, model=model, effort="low", max_tokens=2048, max_rounds=4)


class Session:
    def __init__(self) -> None:
        self.provider = mock_provider()
        self.state = DeskState()

    def desk(self) -> BookingDesk:
        self.state.turn += 1
        return BookingDesk(self.provider, self.state, now)


def answer_with_first_time(body: dict) -> dict:
    """Claude's second turn: reply using the first time the tool returned."""
    result = last_tool_result(body)
    first = result["times"][0]["time"]
    return message([text(f"Yes, Saturday has {first} open. Want me to book one?")])


CHECK = tool_use(
    "check_availability", {"service": "fade", "date": "2026-11-14", "time_of_day": "afternoon"}
)


async def test_tool_loop_checks_availability_and_offers_chips():
    script = ScriptedClaude(
        [message([thinking(), CHECK], stop_reason="tool_use"), answer_with_first_time]
    )
    session = Session()
    assert script.betas == []  # nothing sent yet
    reply = await receptionist(script).reply(
        session.desk(), "Is Saturday afternoon open for a skin fade?", [], system=SYSTEM
    )

    first, second = script.bodies
    assert script.betas == ["", ""]  # Haiku 5.5 has no server-side fallback
    # Request shape: tools are strict, effort is set, no sampling params or forced tool choice.
    assert first["model"] == "claude-haiku-5-5"
    assert first["output_config"] == {"effort": "low"}
    assert first["system"] == SYSTEM
    assert {t["name"] for t in first["tools"]} == {
        "list_services",
        "check_availability",
        "request_booking",
        "confirm_booking",
    }
    assert all(t["strict"] for t in first["tools"])
    assert "temperature" not in first and "tool_choice" not in first and "thinking" not in first
    context = first["messages"][-1]["content"][0]["text"]
    assert "Today is Monday, 2026-11-09" in context
    # The assistant turn goes back unchanged, thinking block first, then the tool result.
    assert second["messages"][-2]["content"][0] == {
        "type": "thinking",
        "thinking": "",
        "signature": "sig-1",
    }
    tool_result = second["messages"][-1]["content"][0]
    assert tool_result["tool_use_id"] == "toolu_1" and "is_error" not in tool_result
    result = last_tool_result(second)
    real = {
        s.start.strftime("%-I:%M %p")
        for s in await session.provider.find_slots("kingsway_svc_fade", session.state.day)
    }
    assert {t["time"] for t in result["times"]} <= real

    words = next(e for e in reply if isinstance(e, TextEvent)).text
    assert words.startswith("Yes, Saturday has")
    chips = next(e for e in reply if isinstance(e, ChoicesEvent))
    assert [o.label for o in chips.options] == [t["time"] for t in result["times"]]


async def test_invented_times_are_replaced():
    script = ScriptedClaude(
        [
            message([CHECK], stop_reason="tool_use"),
            message([text("Saturday has 11:11 PM open, want it?")]),
        ]
    )
    reply = await receptionist(script).reply(Session().desk(), "fade saturday?", [], system=SYSTEM)
    words = next(e for e in reply if isinstance(e, TextEvent)).text
    assert "11:11" not in words
    assert words == "Here are the open times I found. Want me to book one?"


async def test_times_without_a_tool_call_are_never_shown():
    script = ScriptedClaude([message([text("Sure, 2:00 PM is free on Saturday.")])])
    reply = await receptionist(script).reply(Session().desk(), "2pm saturday?", [], system=SYSTEM)
    words = next(e for e in reply if isinstance(e, TextEvent)).text
    assert times_in(words) == set()


async def test_staging_and_confirming_in_one_message_is_refused():
    session = Session()
    # First message: check availability.
    script = ScriptedClaude([message([CHECK], stop_reason="tool_use"), answer_with_first_time])
    await receptionist(script).reply(session.desk(), "fade saturday", [], system=SYSTEM)
    slot_id = next(iter(session.state.offered))

    stage = tool_use(
        "request_booking",
        {"slot_id": slot_id, "name": "Alex Chen", "email": "alex@example.com", "phone": ""},
        "toolu_2",
    )
    confirm = tool_use("confirm_booking", {}, "toolu_3")
    script = ScriptedClaude(
        [
            message([stage, confirm], stop_reason="tool_use"),
            message([text("Here's the summary. Shall I book it?")]),
        ]
    )
    reply = await receptionist(script).reply(
        session.desk(), "the first one, Alex Chen alex@example.com", [], system=SYSTEM
    )
    results = script.bodies[1]["messages"][-1]["content"]
    assert len(results) == 2  # both results in one user message
    assert "is_error" not in results[0]
    assert results[1]["is_error"] is True and "not_confirmed_yet" in results[1]["content"]
    assert session.provider.bookings == []
    pending = next(e for e in reply if isinstance(e, BookingEvent))
    assert pending.status == "pending"

    # Next message: the visitor says yes, so confirm_booking may write it.
    script = ScriptedClaude(
        [
            message([tool_use("confirm_booking", {}, "toolu_4")], stop_reason="tool_use"),
            lambda body: message(
                [text(f"Done! Your reference is {last_tool_result(body)['reference']}.")]
            ),
        ]
    )
    reply = await receptionist(script).reply(session.desk(), "yes", [], system=SYSTEM)
    assert (
        "Waiting for the visitor to confirm"
        in script.bodies[0]["messages"][-1]["content"][0]["text"]
    )
    assert len(session.provider.bookings) == 1
    assert next(e for e in reply if isinstance(e, BookingEvent)).status == "confirmed"


async def test_invalid_tool_input_returns_an_error_result():
    bad = tool_use("check_availability", {"service": "fade", "date": "saturday"})
    script = ScriptedClaude(
        [
            message([bad], stop_reason="tool_use"),
            message([text("Which date did you mean?")]),
        ]
    )
    await receptionist(script).reply(Session().desk(), "fade?", [], system=SYSTEM)
    result = script.bodies[1]["messages"][-1]["content"][0]
    assert result["is_error"] is True and "invalid_input" in result["content"]


async def test_unoffered_slot_cannot_be_staged():
    stage = tool_use(
        "request_booking",
        {"slot_id": "fade-202611141400", "name": "A B", "email": "a@b.co", "phone": ""},
    )
    script = ScriptedClaude(
        [message([stage], stop_reason="tool_use"), message([text("Let me check first.")])]
    )
    session = Session()
    await receptionist(script).reply(session.desk(), "book 2pm", [], system=SYSTEM)
    assert "unknown_slot" in script.bodies[1]["messages"][-1]["content"][0]["content"]
    assert session.state.pending is None


async def test_refusal_raises_without_fallback():
    script = ScriptedClaude([message([], stop_reason="refusal")])
    with pytest.raises(ProviderError) as exc:
        await receptionist(script).reply(Session().desk(), "hi", [], system=SYSTEM)
    assert exc.value.code == "refused" and not exc.value.fallback_ok


async def test_opus_uses_the_server_side_refusal_fallback():
    script = ScriptedClaude([message([text("Which day would you like?")])])
    await receptionist(script, model="claude-opus-5-5").reply(
        Session().desk(), "book", [], system=SYSTEM
    )
    assert FALLBACK_BETA in script.betas[0]
    assert script.bodies[0]["fallbacks"] == "default"


async def test_api_errors_become_provider_errors():
    def fail(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(429, json={"type": "error", "error": {"type": "rate_limit_error"}})

    client = anthropic.AsyncAnthropic(
        api_key="k",
        max_retries=0,
        http_client=anthropic.DefaultAsyncHttpxClient(transport=httpx2.MockTransport(fail)),
    )
    bot = ClaudeReceptionist(client, model="claude-haiku-5-5")
    with pytest.raises(ProviderError) as exc:
        await bot.reply(Session().desk(), "book", [], system=SYSTEM)
    assert exc.value.code == "provider_busy" and exc.value.fallback_ok
