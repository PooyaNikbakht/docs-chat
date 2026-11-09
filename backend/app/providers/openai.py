"""OpenAI adapter: structured output of answer segments, each citing chunk ids.

The streamed JSON is parsed as it arrives (keeping unfinished strings), so segment text
streams token by token. We parse it ourselves rather than with the SDK's strict stream helper,
so OpenAI-compatible hosts (Cloudflare Workers AI and others) work too: one malformed partial
chunk from an open model is skipped instead of failing the whole answer.
When a segment is complete, its chunk ids are mapped to pages and quotes; unknown ids
are dropped.
"""

import logging
from collections.abc import AsyncIterator, Sequence
from typing import Any

import jiter
import openai

from app.models import AnswerEvent, Chunk, TextEvent, Turn
from app.providers.base import (
    DOCUMENT_PERSONA,
    CitationBuilder,
    Persona,
    ProviderError,
    best_quote,
    passages_block,
)
from app.settings import ProviderName

logger = logging.getLogger(__name__)

SEGMENT_INSTRUCTIONS = (
    "\n\nReturn the answer as segments. Each segment is one claim or sentence, with the ids "
    "of the passages that support it in chunk_ids. If the passages don't cover the question, "
    "return one segment with the sentence above and an empty chunk_ids list."
)


def instructions(persona: Persona) -> str:
    return persona.system_prompt + SEGMENT_INSTRUCTIONS


# Strict JSON schema for the answer: a list of segments, each with its supporting chunk ids.
ANSWER_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "StructuredAnswer",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "answer_segments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "chunk_ids": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["text", "chunk_ids"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["answer_segments"],
            "additionalProperties": False,
        },
    },
}


class OpenAIProvider:
    name: ProviderName = "openai"

    def __init__(self, client: openai.AsyncOpenAI, *, model: str) -> None:
        if not model:
            raise ValueError("OPENAI_MODEL is required for the OpenAI provider")
        self.client = client
        self.model = model

    def build_messages(
        self,
        question: str,
        chunks: Sequence[Chunk],
        history: Sequence[Turn],
        persona: Persona = DOCUMENT_PERSONA,
    ) -> list[dict[str, str]]:
        messages = [{"role": "system", "content": instructions(persona)}]
        for turn in history:
            if turn.answer:
                messages.append({"role": "user", "content": turn.question})
                messages.append({"role": "assistant", "content": turn.answer})
        messages.append(
            {
                "role": "user",
                "content": f"Passages:\n\n{passages_block(chunks)}\n\nQuestion: {question}",
            }
        )
        return messages

    async def stream_answer(
        self,
        question: str,
        chunks: Sequence[Chunk],
        history: Sequence[Turn],
        persona: Persona = DOCUMENT_PERSONA,
    ) -> AsyncIterator[AnswerEvent]:
        by_id = {c.chunk_id: c for c in chunks}
        tracker = _SegmentTracker(by_id)
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=self.build_messages(question, chunks, history, persona),  # type: ignore[arg-type]
                response_format=ANSWER_FORMAT,  # type: ignore[arg-type]
                stream=True,
            )
            content = ""
            async for chunk in stream:
                if not chunk.choices:
                    continue
                choice = chunk.choices[0]
                if (
                    getattr(choice.delta, "refusal", None)
                    or choice.finish_reason == "content_filter"
                ):
                    raise ProviderError(
                        "refused", "The model declined to answer this question.", fallback_ok=False
                    )
                piece = choice.delta.content
                if piece is not None and piece != "":
                    # Some OpenAI-compatible hosts send a number token as a JSON number.
                    content += str(piece)
                    for out in tracker.update(_partial_segments(content)):
                        yield out
                if choice.finish_reason == "length":
                    raise ProviderError("provider_error", "The answer was cut off.")
            for out in tracker.update(_final_segments(content), final=True):
                yield out
        except openai.APIConnectionError as exc:  # includes timeouts
            raise ProviderError("provider_unavailable", "Couldn't reach OpenAI.") from exc
        except openai.RateLimitError as exc:
            raise ProviderError("provider_busy", "OpenAI is busy right now.") from exc
        except (openai.AuthenticationError, openai.PermissionDeniedError) as exc:
            raise ProviderError("provider_auth", "The OpenAI API key was rejected.") from exc
        except openai.APIStatusError as exc:
            logger.warning("OpenAI API error %s: %s", exc.status_code, exc.message)
            raise ProviderError("provider_error", "OpenAI returned an error.") from exc


def _final_segments(content: str) -> list[Any]:
    """The complete answer; falls back to a partial parse if the model's JSON is slightly off."""
    try:
        parsed = jiter.from_json(content.encode())
    except ValueError:
        return _partial_segments(content)
    return (parsed.get("answer_segments") or []) if isinstance(parsed, dict) else []


def _partial_segments(snapshot: str) -> list[Any]:
    """Parse the JSON so far, keeping unfinished strings so text can stream."""
    try:
        parsed = jiter.from_json(snapshot.encode(), partial_mode="trailing-strings")
    except ValueError:
        return []
    return (parsed.get("answer_segments") or []) if isinstance(parsed, dict) else []


class _SegmentTracker:
    """Turns successive partial parses of `answer_segments` into text and citation events."""

    def __init__(self, chunks_by_id: dict[str, Chunk]) -> None:
        self.chunks = chunks_by_id
        self.citations = CitationBuilder()
        self.sent_text: list[str] = []  # text already emitted, per segment
        self.closed = 0  # segments whose citations were emitted

    def update(self, segments: list[Any], *, final: bool = False) -> list[AnswerEvent]:
        out: list[AnswerEvent] = []
        for i, seg in enumerate(segments):
            if not isinstance(seg, dict):
                continue
            if i == len(self.sent_text):
                self.sent_text.append("")
            if i < self.closed:
                continue
            text = seg.get("text") or ""
            sent = self.sent_text[i]
            if text.startswith(sent) and len(text) > len(sent):
                delta = text[len(sent) :]
                if not sent and i > 0 and not delta[0].isspace():
                    delta = " " + delta
                out.append(TextEvent(text=delta))
                self.sent_text[i] = text
            # A segment is complete once the next one starts, or when parsing is done.
            if i < len(segments) - 1 or final:
                out.extend(self._cite(seg))
                self.closed = i + 1
        return out

    def _cite(self, seg: dict[str, Any]) -> list[AnswerEvent]:
        events: list[AnswerEvent] = []
        for chunk_id in seg.get("chunk_ids") or []:
            chunk = self.chunks.get(chunk_id)
            if chunk is None:
                continue  # unknown ids are dropped
            events.append(self.citations.cite(chunk, best_quote(chunk, seg.get("text") or "")))
        return events
