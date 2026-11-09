"""Shared helpers for the booking tests: a fixed clock and Claude message fakes."""

import json
from collections.abc import Callable
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx2

from app.booking.mock import MockBookingProvider

TZ = ZoneInfo("America/Toronto")
# Monday, November 9 2026, 10:00 in Toronto.
NOW = datetime(2026, 11, 9, 10, 0, tzinfo=TZ)
TODAY = NOW.date()
SATURDAY = date(2026, 11, 14)
SUNDAY = date(2026, 11, 15)


def now() -> datetime:
    return NOW


def mock_provider(**kwargs: Any) -> MockBookingProvider:
    return MockBookingProvider(clock=NOW.timestamp, **kwargs)


def message(content: list[dict[str, Any]], stop_reason: str = "end_turn") -> dict[str, Any]:
    return {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "model": "claude-haiku-5-5",
        "content": content,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {"input_tokens": 900, "output_tokens": 40},
    }


def thinking() -> dict[str, Any]:
    return {"type": "thinking", "thinking": "", "signature": "sig-1"}


def tool_use(name: str, args: dict[str, Any], tool_id: str = "toolu_1") -> dict[str, Any]:
    return {"type": "tool_use", "id": tool_id, "name": name, "input": args}


def text(value: str) -> dict[str, Any]:
    return {"type": "text", "text": value}


Step = dict[str, Any] | Callable[[dict[str, Any]], dict[str, Any]]


class ScriptedClaude:
    """Replays one Messages API response per request. A step may be built from the request."""

    def __init__(self, steps: list[Step]) -> None:
        self.steps = list(steps)
        self.bodies: list[dict[str, Any]] = []
        self.betas: list[str] = []

    def handler(self, request: httpx2.Request) -> httpx2.Response:
        body = json.loads(request.content)
        self.bodies.append(body)
        self.betas.append(request.headers.get("anthropic-beta", ""))
        step = self.steps.pop(0)
        payload = step(body) if callable(step) else step
        return httpx2.Response(200, json=payload)


def last_tool_result(body: dict[str, Any]) -> dict[str, Any]:
    """The JSON content of the last tool_result block in a request."""
    blocks = body["messages"][-1]["content"]
    result = next(b for b in reversed(blocks) if b.get("type") == "tool_result")
    return json.loads(result["content"])
