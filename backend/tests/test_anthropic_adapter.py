import pytest

from app.bots import NORTHWIND
from app.models import CitationEvent, TextEvent, Turn
from app.providers.anthropic import FALLBACK_BETA, AnthropicProvider, supports_refusal_fallback
from app.providers.base import DOCUMENT_PERSONA, ProviderError
from tests.fakes import (
    Recorder,
    anthropic_client,
    claude_events,
    error_response,
    sse,
    stream_response,
)

QUESTION = "Can I pause my subscription?"


def pause_chunks(doc):
    return [h.chunk for h in doc.index.search(QUESTION, 6)]


async def collect(provider, chunks, history=()):
    return [e async for e in provider.stream_answer(QUESTION, chunks, list(history))]


async def test_streams_text_and_maps_citations_to_pages(sample_doc):
    chunks = pause_chunks(sample_doc)
    rec = Recorder(stream_response(sse(claude_events(chunks))))
    provider = AnthropicProvider(anthropic_client(rec), model="claude-opus-5-5")

    events = await collect(provider, chunks)

    text = "".join(e.text for e in events if isinstance(e, TextEvent))
    assert text == "Yes, you can pause it for up to 3 months at a time."
    cites = [e for e in events if isinstance(e, CitationEvent)]
    assert len(cites) == 1
    assert cites[0].index == 1
    assert cites[0].chunk_id == chunks[0].chunk_id
    assert cites[0].page == 4  # the subscriptions page, though the chunk starts earlier
    assert cites[0].quote.startswith("You can pause your subscription")
    assert cites[0].quote in cites[0].context
    # The marker comes right after the cited text, before the closing period.
    kinds = [type(e).__name__ for e in events]
    assert kinds[-2:] == ["CitationEvent", "TextEvent"]


async def test_request_shape_for_opus(sample_doc):
    chunks = pause_chunks(sample_doc)
    rec = Recorder(stream_response(sse(claude_events(chunks))))
    provider = AnthropicProvider(anthropic_client(rec), model="claude-opus-5-5", effort="medium")
    history = [Turn("Do you ship to the US?", "Yes, standard shipping takes 4 to 8 days.")]

    await collect(provider, chunks, history)

    body = rec.body
    request = rec.requests[-1]
    assert body["model"] == "claude-opus-5-5"
    assert body["output_config"] == {"effort": "medium"}
    assert body["stream"] is True
    # Not allowed on this model family: sampling params, thinking config, prefill.
    for key in ("temperature", "top_p", "top_k", "thinking", "tool_choice"):
        assert key not in body
    assert body["messages"][-1]["role"] == "user"
    # Server-side refusal fallback is on for Opus.
    assert body["fallbacks"] == "default"
    assert FALLBACK_BETA in request.headers["anthropic-beta"]
    # History is plain text, and documents only appear in the latest user turn.
    assert body["messages"][0] == {"role": "user", "content": "Do you ship to the US?"}
    assert body["messages"][1] == {
        "role": "assistant",
        "content": "Yes, standard shipping takes 4 to 8 days.",
    }
    content = body["messages"][-1]["content"]
    docs = [b for b in content if b["type"] == "document"]
    assert len(docs) == len(chunks)
    assert docs[0]["citations"] == {"enabled": True}
    assert docs[0]["source"] == {"type": "text", "media_type": "text/plain", "data": chunks[0].text}
    assert content[-1] == {"type": "text", "text": QUESTION}


async def test_haiku_has_no_fallback_parameter(sample_doc):
    chunks = pause_chunks(sample_doc)
    rec = Recorder(stream_response(sse(claude_events(chunks, model="claude-haiku-5-5"))))
    provider = AnthropicProvider(anthropic_client(rec), model="claude-haiku-5-5")

    events = await collect(provider, chunks)

    assert any(isinstance(e, CitationEvent) for e in events)
    assert "fallbacks" not in rec.body
    assert "anthropic-beta" not in rec.requests[-1].headers
    assert rec.body["output_config"] == {"effort": "medium"}


async def test_system_prompt_comes_from_the_persona(sample_doc):
    chunks = pause_chunks(sample_doc)
    rec = Recorder(stream_response(sse(claude_events(chunks))))
    provider = AnthropicProvider(anthropic_client(rec), model="claude-haiku-5-5")

    await collect(provider, chunks)
    assert rec.body["system"] == DOCUMENT_PERSONA.system_prompt

    rec2 = Recorder(stream_response(sse(claude_events(chunks))))
    provider = AnthropicProvider(anthropic_client(rec2), model="claude-haiku-5-5")
    events = [e async for e in provider.stream_answer(QUESTION, chunks, [], NORTHWIND.persona)]
    assert rec2.body["system"] == NORTHWIND.persona.system_prompt
    assert any(isinstance(e, CitationEvent) for e in events)


def test_fallback_support_by_model():
    assert supports_refusal_fallback("claude-opus-5-5")
    assert not supports_refusal_fallback("claude-haiku-5-5")


async def test_fallback_block_is_ignored(sample_doc):
    chunks = pause_chunks(sample_doc)
    rec = Recorder(stream_response(sse(claude_events(chunks, fallback_block=True))))
    provider = AnthropicProvider(anthropic_client(rec), model="claude-opus-5-5")

    events = await collect(provider, chunks)

    assert sum(isinstance(e, CitationEvent) for e in events) == 1


async def test_refusal_raises_without_fallback_to_mock(sample_doc):
    chunks = pause_chunks(sample_doc)
    rec = Recorder(stream_response(sse(claude_events(chunks, stop_reason="refusal"))))
    provider = AnthropicProvider(anthropic_client(rec), model="claude-opus-5-5")

    with pytest.raises(ProviderError) as err:
        await collect(provider, chunks)
    assert err.value.code == "refused"
    assert not err.value.fallback_ok


async def test_unknown_document_index_is_dropped(sample_doc):
    chunks = pause_chunks(sample_doc)[:1]
    events = claude_events(chunks)
    for e in events:
        if e.get("delta", {}).get("type") == "citations_delta":
            e["delta"]["citation"]["document_index"] = 7
    rec = Recorder(stream_response(sse(events)))
    provider = AnthropicProvider(anthropic_client(rec), model="claude-opus-5-5")

    out = await collect(provider, chunks)

    assert not any(isinstance(e, CitationEvent) for e in out)


@pytest.mark.parametrize(
    ("status", "error_type", "code"),
    [
        (401, "authentication_error", "provider_auth"),
        (429, "rate_limit_error", "provider_busy"),
        (529, "overloaded_error", "provider_error"),
        (400, "invalid_request_error", "provider_error"),
    ],
)
async def test_api_errors_become_provider_errors(sample_doc, status, error_type, code):
    rec = Recorder(
        error_response(status, {"type": "error", "error": {"type": error_type, "message": "x"}})
    )
    provider = AnthropicProvider(anthropic_client(rec), model="claude-opus-5-5")

    with pytest.raises(ProviderError) as err:
        await collect(provider, pause_chunks(sample_doc))
    assert err.value.code == code
    assert err.value.fallback_ok
