"""Claude adapter: retrieved chunks go in as plain-text documents with citations enabled.

Claude returns `char_location` citations that point at a document index and a character
range. Each document is one chunk, so the index gives the chunk and the offset gives the page.
"""

import logging
from collections.abc import AsyncIterator, Sequence
from typing import Any

import anthropic

from app.models import AnswerEvent, Chunk, CitationEvent, TextEvent, Turn
from app.providers.base import DOCUMENT_PERSONA, CitationBuilder, Persona, ProviderError
from app.settings import ProviderName

logger = logging.getLogger(__name__)

# Models that accept the server-side refusal fallback (`fallbacks: "default"`).
# Claude Haiku 5.5 has no server-side fallback, so it is not listed.
FALLBACK_MODELS = frozenset({"claude-opus-5-5", "claude-opus-5"})
FALLBACK_BETA = "server-side-fallback-2026-07-01"


def supports_refusal_fallback(model: str) -> bool:
    return model in FALLBACK_MODELS


class AnthropicProvider:
    name: ProviderName = "anthropic"

    def __init__(
        self,
        client: anthropic.AsyncAnthropic,
        *,
        model: str,
        effort: str = "medium",
        max_tokens: int = 4096,
    ) -> None:
        self.client = client
        self.model = model
        self.effort = effort
        self.max_tokens = max_tokens

    def build_params(
        self,
        question: str,
        chunks: Sequence[Chunk],
        history: Sequence[Turn],
        persona: Persona = DOCUMENT_PERSONA,
    ) -> dict[str, Any]:
        messages: list[dict[str, Any]] = []
        for turn in history:
            if turn.answer:
                messages.append({"role": "user", "content": turn.question})
                # Plain text only: cited blocks are never echoed back.
                messages.append({"role": "assistant", "content": turn.answer})
        documents = [
            {
                "type": "document",
                "source": {"type": "text", "media_type": "text/plain", "data": c.text},
                "title": _title(i, c),
                "citations": {"enabled": True},
            }
            for i, c in enumerate(chunks)
        ]
        messages.append(
            {"role": "user", "content": [*documents, {"type": "text", "text": question}]}
        )
        # No temperature, top_p, thinking or prefill: thinking is always on for this model
        # family and effort is the control.
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": persona.system_prompt,
            "messages": messages,
            "output_config": {"effort": self.effort},
        }

    def _open_stream(self, params: dict[str, Any]) -> Any:
        if supports_refusal_fallback(self.model):
            return self.client.beta.messages.stream(
                **params, betas=[FALLBACK_BETA], fallbacks="default"
            )
        return self.client.messages.stream(**params)

    async def stream_answer(
        self,
        question: str,
        chunks: Sequence[Chunk],
        history: Sequence[Turn],
        persona: Persona = DOCUMENT_PERSONA,
    ) -> AsyncIterator[AnswerEvent]:
        params = self.build_params(question, chunks, history, persona)
        citations = CitationBuilder()
        pending: list[CitationEvent] = []
        stop_reason: str | None = None
        try:
            async with self._open_stream(params) as stream:
                async for event in stream:
                    if event.type == "text":
                        yield TextEvent(text=event.text)
                    elif event.type == "citation":
                        mapped = _map_citation(event.citation, chunks, citations)
                        if mapped is not None:
                            pending.append(mapped)
                    elif event.type == "content_block_stop" and pending:
                        # Place markers after the text they support.
                        for c in pending:
                            yield c
                        pending.clear()
                    elif event.type == "message_delta" and event.delta.stop_reason:
                        stop_reason = event.delta.stop_reason
        except anthropic.APIConnectionError as exc:  # includes timeouts
            raise ProviderError("provider_unavailable", "Couldn't reach Claude.") from exc
        except anthropic.RateLimitError as exc:
            raise ProviderError("provider_busy", "Claude is busy right now.") from exc
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as exc:
            raise ProviderError("provider_auth", "The Claude API key was rejected.") from exc
        except anthropic.APIStatusError as exc:
            logger.warning("Claude API error %s: %s", exc.status_code, exc.message)
            raise ProviderError("provider_error", "Claude returned an error.") from exc

        for c in pending:
            yield c
        if stop_reason == "refusal":
            raise ProviderError(
                "refused", "Claude declined to answer this question.", fallback_ok=False
            )


def _title(i: int, chunk: Chunk) -> str:
    pages = (
        f"page {chunk.page_start}"
        if chunk.page_start == chunk.page_end
        else f"pages {chunk.page_start}-{chunk.page_end}"
    )
    return f"Passage {i + 1} ({pages})"


def _map_citation(
    citation: Any, chunks: Sequence[Chunk], builder: CitationBuilder
) -> CitationEvent | None:
    """Map a Claude citation to our normalized event. Unknown shapes are dropped."""
    if getattr(citation, "type", None) != "char_location":
        return None
    idx = citation.document_index
    if not 0 <= idx < len(chunks):
        return None
    chunk = chunks[idx]
    quote = citation.cited_text or chunk.text[citation.start_char_index : citation.end_char_index]
    event = builder.cite(chunk, quote)
    # Claude gives us the exact offset, which is more precise than searching for the quote.
    raw = chunk.text[citation.start_char_index : citation.end_char_index]
    offset = citation.start_char_index + len(raw) - len(raw.lstrip())
    return event.model_copy(update={"page": chunk.page_at(offset)})
