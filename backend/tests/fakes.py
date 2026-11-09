"""Recorded-shape fakes: real SDK clients talking to an in-memory HTTP transport."""

import json
from collections.abc import Callable
from typing import Any

import anthropic
import httpx2
import openai

from app.models import Chunk


def sse(events: list[dict[str, Any]], *, named: bool = True) -> bytes:
    """Frame events as server-sent events, as the provider APIs send them."""
    out = []
    for e in events:
        head = f"event: {e['type']}\n" if named else ""
        out.append(f"{head}data: {json.dumps(e)}\n\n")
    return "".join(out).encode()


class Recorder:
    """An httpx2 transport that records requests and replays a canned response."""

    def __init__(self, respond: Callable[[httpx2.Request], httpx2.Response]) -> None:
        self.requests: list[httpx2.Request] = []
        self._respond = respond

    def handler(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        return self._respond(request)

    @property
    def body(self) -> dict[str, Any]:
        return json.loads(self.requests[-1].content)


def stream_response(payload: bytes) -> Callable[[httpx2.Request], httpx2.Response]:
    return lambda _: httpx2.Response(
        200, headers={"content-type": "text/event-stream"}, content=payload
    )


def error_response(
    status: int, body: dict[str, Any]
) -> Callable[[httpx2.Request], httpx2.Response]:
    return lambda _: httpx2.Response(status, json=body)


def anthropic_client(recorder: Recorder) -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(
        api_key="test-key",
        max_retries=0,
        http_client=anthropic.DefaultAsyncHttpxClient(
            transport=httpx2.MockTransport(recorder.handler)
        ),
    )


def openai_client(recorder: Recorder) -> openai.AsyncOpenAI:
    return openai.AsyncOpenAI(
        api_key="test-key",
        max_retries=0,
        http_client=openai.DefaultAsyncHttpxClient(
            transport=httpx2.MockTransport(recorder.handler)
        ),
    )


# ---- Claude: a streamed answer with one cited text block ----


def claude_events(
    chunks: list[Chunk],
    *,
    model: str = "claude-opus-5-5",
    doc_index: int = 0,
    quote: str = "You can pause your subscription for up to 3 months",
    stop_reason: str = "end_turn",
    fallback_block: bool = False,
) -> list[dict[str, Any]]:
    text = chunks[doc_index].text
    start = text.find(quote)
    assert start >= 0, "quote must come from the chunk"
    events: list[dict[str, Any]] = [
        {
            "type": "message_start",
            "message": {
                "id": "msg_test",
                "type": "message",
                "role": "assistant",
                "model": model,
                "content": [],
                "stop_reason": None,
                "stop_sequence": None,
                "usage": {"input_tokens": 1200, "output_tokens": 1},
            },
        },
    ]
    idx = 0
    if fallback_block:
        events += [
            {
                "type": "content_block_start",
                "index": idx,
                "content_block": {
                    "type": "fallback",
                    "from": {"model": model},
                    "to": {"model": "claude-opus-5"},
                    "trigger": {"type": "refusal", "category": None},
                },
            },
            {"type": "content_block_stop", "index": idx},
        ]
        idx += 1
    events += [
        {
            "type": "content_block_start",
            "index": idx,
            "content_block": {"type": "thinking", "thinking": "", "signature": ""},
        },
        {
            "type": "content_block_delta",
            "index": idx,
            "delta": {"type": "signature_delta", "signature": "sig"},
        },
        {"type": "content_block_stop", "index": idx},
        {
            "type": "content_block_start",
            "index": idx + 1,
            "content_block": {"type": "text", "text": ""},
        },
        {
            "type": "content_block_delta",
            "index": idx + 1,
            "delta": {"type": "text_delta", "text": "Yes, "},
        },
        {"type": "content_block_stop", "index": idx + 1},
        {
            "type": "content_block_start",
            "index": idx + 2,
            "content_block": {"type": "text", "text": "", "citations": []},
        },
        {
            "type": "content_block_delta",
            "index": idx + 2,
            "delta": {
                "type": "citations_delta",
                "citation": {
                    "type": "char_location",
                    "cited_text": quote,
                    "document_index": doc_index,
                    "document_title": "Passage 1",
                    "start_char_index": start,
                    "end_char_index": start + len(quote),
                },
            },
        },
        {
            "type": "content_block_delta",
            "index": idx + 2,
            "delta": {"type": "text_delta", "text": "you can pause it for up to 3 months"},
        },
        {
            "type": "content_block_delta",
            "index": idx + 2,
            "delta": {"type": "text_delta", "text": " at a time"},
        },
        {"type": "content_block_stop", "index": idx + 2},
        {
            "type": "content_block_start",
            "index": idx + 3,
            "content_block": {"type": "text", "text": ""},
        },
        {
            "type": "content_block_delta",
            "index": idx + 3,
            "delta": {"type": "text_delta", "text": "."},
        },
        {"type": "content_block_stop", "index": idx + 3},
        {
            "type": "message_delta",
            "delta": {"stop_reason": stop_reason, "stop_sequence": None},
            "usage": {"output_tokens": 60},
        },
        {"type": "message_stop"},
    ]
    return events


# ---- OpenAI: structured output streamed as JSON text deltas ----


def openai_chunks(content: str, *, model: str = "test-model", pieces: int = 7) -> bytes:
    size = max(1, len(content) // pieces)
    parts = [content[i : i + size] for i in range(0, len(content), size)]
    base = {"id": "chatcmpl-test", "object": "chat.completion.chunk", "created": 0, "model": model}
    events = [
        {**base, "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}}]},
        *(
            {**base, "choices": [{"index": 0, "delta": {"content": p}, "finish_reason": None}]}
            for p in parts
        ),
        {**base, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]},
    ]
    return sse(events, named=False) + b"data: [DONE]\n\n"
