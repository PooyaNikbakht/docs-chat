"""Answer orchestration: retrieve, check the threshold, pick a provider, fall back, stream."""

import logging
import re
from collections.abc import AsyncIterator, Callable, Sequence

from app.limits import LiveQuota
from app.models import (
    CitationEvent,
    Document,
    DoneEvent,
    ErrorEvent,
    MetaEvent,
    StreamEvent,
    TextEvent,
    Turn,
)
from app.providers.base import DOCUMENT_PERSONA, AnswerProvider, Persona, ProviderError
from app.retrieval.base import Retriever
from app.retrieval.query import retrieve

logger = logging.getLogger(__name__)

PROVIDER_DOWN_NOTICE = "The AI provider isn't available right now, so this answer uses demo mode."

# Questions about the assistant itself, which no help center passage answers.
_ABOUT_QUESTION = re.compile(
    r"^\W*(?:"
    r"(?:what|how)\s+(?:can|could|do|will)\s+you\s+(?:help|do|assist|answer)"
    r"|what\s+(?:can|could|should)\s+i\s+ask"
    r"|what\s+(?:do|can)\s+you\s+know"
    r"|(?:who|what)\s+are\s+you"
    r"|(?:help|hi|hello|hey)\W*$"
    r")",
    re.IGNORECASE,
)


def is_about_question(question: str) -> bool:
    return bool(_ABOUT_QUESTION.match(question.strip()))


class Answerer:
    def __init__(
        self,
        provider: AnswerProvider,
        fallback: AnswerProvider,
        quota: LiveQuota,
        *,
        top_k: int,
        min_score: float,
        live_min_score: float | None = None,
        whole_document_max_words: int = 0,
        fallback_to_mock: bool = True,
    ) -> None:
        self.provider = provider
        self.fallback = fallback
        self.quota = quota
        self.top_k = top_k
        self.min_score = min_score
        self.live_min_score = min_score if live_min_score is None else live_min_score
        self.whole_document_max_words = whole_document_max_words
        self.fallback_to_mock = fallback_to_mock

    def _fits_whole(self, doc: Document) -> bool:
        words = sum(len(chunk.text.split()) for chunk in doc.chunks)
        return 0 < words <= self.whole_document_max_words

    async def stream(
        self,
        doc: Document,
        question: str,
        history: Sequence[Turn],
        *,
        client_ip: str,
        remember: Callable[[str], None],
        persona: Persona = DOCUMENT_PERSONA,
    ) -> AsyncIterator[StreamEvent]:
        if persona.about and is_about_question(question):
            # About the assistant, not the business: answer from the persona, no model call.
            yield MetaEvent(provider=self.provider.name)
            yield TextEvent(text=persona.about)
            yield DoneEvent(provider=self.provider.name, grounded=False, citations=0, handoff=False)
            remember(persona.about)
            return

        retriever: Retriever = doc.index
        result = retrieve(retriever, question, history, k=self.top_k, min_score=self.min_score)
        best = result.hits[0].score if result.hits else 0.0
        chunks = [hit.chunk for hit in result.hits]
        if best < self.live_min_score and self._fits_whole(doc):
            # Keywords found nothing, but the document is short: a live model can read all of it.
            chunks, best = list(doc.chunks), self.live_min_score
        provider, notice = self.provider, None
        if provider.name != "mock" and best >= self.live_min_score:
            reason = self.quota.take(client_ip)
            if reason and self.fallback_to_mock:
                provider, notice = self.fallback, reason

        # Demo mode can only quote passages, so it needs a clear match. A live model reads the
        # passages and says "not found" itself, so it only needs some overlap.
        answerable = result.answerable if provider.name == "mock" else best >= self.live_min_score
        if not answerable:
            # Nothing in the document is close enough: answer without calling a model.
            yield MetaEvent(provider=provider.name, notice=notice)
            yield TextEvent(text=persona.not_found)
            yield DoneEvent(provider=provider.name, grounded=False, citations=0, handoff=True)
            remember(persona.not_found)
            return

        parts: list[str] = []
        citations: set[int] = set()
        started = False
        try:
            async for event in provider.stream_answer(question, chunks, history, persona):
                if not started:
                    started = True
                    yield MetaEvent(provider=provider.name, notice=notice)
                if isinstance(event, TextEvent):
                    parts.append(event.text)
                elif isinstance(event, CitationEvent):
                    citations.add(event.index)
                yield event
        except ProviderError as exc:
            can_fall_back = (
                not started
                and exc.fallback_ok
                and self.fallback_to_mock
                and provider is not self.fallback
            )
            if not can_fall_back:
                if not started:
                    yield MetaEvent(provider=provider.name)
                yield ErrorEvent(code=exc.code, message=exc.message)
                return
            logger.warning("Provider %s failed (%s); using mock mode", provider.name, exc.code)
            provider, notice = self.fallback, PROVIDER_DOWN_NOTICE
            yield MetaEvent(provider=provider.name, notice=notice)
            started = True
            if not result.answerable:
                # Too weak a match for demo mode to quote from.
                yield TextEvent(text=persona.not_found)
                yield DoneEvent(provider=provider.name, grounded=False, citations=0, handoff=True)
                remember(persona.not_found)
                return
            async for event in provider.stream_answer(question, chunks, history, persona):
                if isinstance(event, TextEvent):
                    parts.append(event.text)
                elif isinstance(event, CitationEvent):
                    citations.add(event.index)
                yield event
        except Exception:
            logger.exception("Answer stream failed")
            if not started:
                yield MetaEvent(provider=provider.name)
            yield ErrorEvent(code="internal_error", message="Something went wrong on our side.")
            return

        answer = "".join(parts).strip()
        remember(answer)
        grounded = bool(citations)
        yield DoneEvent(
            provider=provider.name,
            grounded=grounded,
            citations=len(citations),
            handoff=not grounded,
        )
