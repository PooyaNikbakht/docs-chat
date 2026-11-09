import json

import pytest

from app.models import CitationEvent, TextEvent, Turn
from app.providers.base import ProviderError
from app.providers.openai import OpenAIProvider, _SegmentTracker
from tests.fakes import Recorder, error_response, openai_chunks, openai_client, stream_response

QUESTION = "Can I pause my subscription?"


def pause_chunks(doc):
    return [h.chunk for h in doc.index.search(QUESTION, 6)]


def answer_json(chunk_id: str) -> str:
    return json.dumps(
        {
            "answer_segments": [
                {
                    "text": "You can pause your subscription for up to 3 months.",
                    "chunk_ids": [chunk_id],
                },
                {
                    "text": "You can also skip a single delivery.",
                    "chunk_ids": [chunk_id, "made-up-id"],
                },
            ]
        }
    )


async def collect(provider, chunks, history=()):
    return [e async for e in provider.stream_answer(QUESTION, chunks, list(history))]


async def test_streams_segments_and_maps_chunk_ids(sample_doc):
    chunks = pause_chunks(sample_doc)
    rec = Recorder(stream_response(openai_chunks(answer_json(chunks[0].chunk_id))))
    provider = OpenAIProvider(openai_client(rec), model="test-model")

    events = await collect(provider, chunks)

    texts = [e.text for e in events if isinstance(e, TextEvent)]
    assert len(texts) > 2  # streamed in pieces, not in one go
    assert "".join(texts) == (
        "You can pause your subscription for up to 3 months. You can also skip a single delivery."
    )
    cites = [e for e in events if isinstance(e, CitationEvent)]
    # The unknown id is dropped; both segments cite the subscriptions page.
    assert [c.chunk_id for c in cites] == [chunks[0].chunk_id, chunks[0].chunk_id]
    assert [c.page for c in cites] == [4, 4]
    assert cites[0].quote.startswith("You can pause your subscription")
    assert cites[1].quote.startswith("Skip any single delivery")
    assert [c.index for c in cites] == [1, 2]


async def test_request_uses_structured_output(sample_doc):
    chunks = pause_chunks(sample_doc)
    rec = Recorder(stream_response(openai_chunks(answer_json(chunks[0].chunk_id))))
    provider = OpenAIProvider(openai_client(rec), model="test-model")

    await collect(provider, chunks, [Turn("Do you ship to the US?", "Yes.")])

    body = rec.body
    assert body["model"] == "test-model"
    fmt = body["response_format"]
    assert fmt["type"] == "json_schema"
    assert fmt["json_schema"]["strict"] is True
    assert "answer_segments" in fmt["json_schema"]["schema"]["properties"]
    roles = [m["role"] for m in body["messages"]]
    assert roles == ["system", "user", "assistant", "user"]
    assert f'id="{chunks[0].chunk_id}"' in body["messages"][-1]["content"]


def test_model_is_required():
    with pytest.raises(ValueError):
        OpenAIProvider(object(), model="")  # type: ignore[arg-type]


async def test_refusal_raises(sample_doc):
    base = {"id": "x", "object": "chat.completion.chunk", "created": 0, "model": "m"}
    events = [
        {**base, "choices": [{"index": 0, "delta": {"role": "assistant", "refusal": "No."}}]},
        {**base, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]},
    ]
    payload = b"".join(f"data: {json.dumps(e)}\n\n".encode() for e in events) + b"data: [DONE]\n\n"
    rec = Recorder(stream_response(payload))
    provider = OpenAIProvider(openai_client(rec), model="m")

    with pytest.raises(ProviderError) as err:
        await collect(provider, pause_chunks(sample_doc))
    assert err.value.code == "refused"


@pytest.mark.parametrize(
    ("status", "code"), [(401, "provider_auth"), (429, "provider_busy"), (500, "provider_error")]
)
async def test_api_errors_become_provider_errors(sample_doc, status, code):
    rec = Recorder(error_response(status, {"error": {"message": "x", "type": "x", "code": None}}))
    provider = OpenAIProvider(openai_client(rec), model="m")

    with pytest.raises(ProviderError) as err:
        await collect(provider, pause_chunks(sample_doc))
    assert err.value.code == code


def test_segment_tracker_handles_partial_parses(sample_doc):
    chunk = sample_doc.chunks[0]
    tracker = _SegmentTracker({chunk.chunk_id: chunk})
    out = tracker.update([{"text": "New emp"}])
    out += tracker.update([{"text": "New employees get 15 days", "chunk_ids": [chunk.chunk_id]}])
    out += tracker.update(
        [{"text": "New employees get 15 days.", "chunk_ids": [chunk.chunk_id]}, {"text": "Also"}]
    )
    out += tracker.update(
        [
            {"text": "New employees get 15 days.", "chunk_ids": [chunk.chunk_id]},
            {"text": "Also more.", "chunk_ids": []},
        ],
        final=True,
    )
    text = "".join(e.text for e in out if isinstance(e, TextEvent))
    assert text == "New employees get 15 days. Also more."
    assert sum(isinstance(e, CitationEvent) for e in out) == 1
