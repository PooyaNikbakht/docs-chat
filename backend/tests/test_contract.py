"""Every provider adapter must emit the same normalized events."""

import json

import pytest

from app.models import CitationEvent, TextEvent
from app.providers.anthropic import AnthropicProvider
from app.providers.mock import MockProvider
from app.providers.openai import OpenAIProvider
from app.retrieval.text import find_loose
from tests.fakes import (
    Recorder,
    anthropic_client,
    claude_events,
    openai_chunks,
    openai_client,
    sse,
    stream_response,
)

QUESTION = "Can I pause my subscription?"


def make_mock(chunks):
    return MockProvider()


def make_claude(chunks):
    rec = Recorder(stream_response(sse(claude_events(chunks))))
    return AnthropicProvider(anthropic_client(rec), model="claude-opus-5-5")


def make_claude_haiku(chunks):
    rec = Recorder(stream_response(sse(claude_events(chunks, model="claude-haiku-5-5"))))
    return AnthropicProvider(anthropic_client(rec), model="claude-haiku-5-5")


def make_openai(chunks):
    content = json.dumps(
        {
            "answer_segments": [
                {"text": "You can pause for up to 3 months.", "chunk_ids": [chunks[0].chunk_id]}
            ]
        }
    )
    rec = Recorder(stream_response(openai_chunks(content)))
    return OpenAIProvider(openai_client(rec), model="test-model")


@pytest.fixture(params=[make_mock, make_claude, make_claude_haiku, make_openai])
def factory(request):
    return request.param


async def test_adapter_contract(sample_doc, factory):
    chunks = [h.chunk for h in sample_doc.index.search(QUESTION, 6)]
    provider = factory(chunks)
    assert provider.name in {"anthropic", "openai", "mock"}

    events = [e async for e in provider.stream_answer(QUESTION, chunks, [])]

    assert events, "an answer must produce events"
    assert all(isinstance(e, TextEvent | CitationEvent) for e in events)
    assert isinstance(events[0], TextEvent), "answers start with text"
    text = "".join(e.text for e in events if isinstance(e, TextEvent))
    assert "3 months" in text

    cites = [e for e in events if isinstance(e, CitationEvent)]
    assert cites, "a grounded answer cites at least one passage"
    by_id = {c.chunk_id: c for c in chunks}
    seen: set[int] = set()
    for c in cites:
        chunk = by_id[c.chunk_id]  # only ids of chunks we passed in
        assert chunk.page_start <= c.page <= chunk.page_end
        assert find_loose(chunk.text, c.quote), "quote must come from the chunk"
        assert find_loose(c.context, c.quote), "context must contain the quote"
        assert c.index == len(seen) + 1 or c.index in seen, "indices count up from 1"
        seen.add(c.index)
    assert any(c.page == 4 for c in cites), "the answer cites the subscriptions page"
