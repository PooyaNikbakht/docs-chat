"""Deterministic, key-free adapter. Answers with the best-matching sentences, cited."""

import asyncio
import math
import re
from collections import Counter
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass

from app.models import AnswerEvent, Chunk, TextEvent, Turn
from app.providers.base import DOCUMENT_PERSONA, CitationBuilder, Persona
from app.retrieval.text import split_sentences, tokenize
from app.settings import ProviderName

_NOISE = re.compile(r"^(fictional sample|page \d+)", re.IGNORECASE)


class MockProvider:
    name: ProviderName = "mock"

    def __init__(self, delay_seconds: float = 0.0, max_sentences: int = 2) -> None:
        self.delay = delay_seconds
        self.max_sentences = max_sentences

    async def stream_answer(
        self,
        question: str,
        chunks: Sequence[Chunk],
        history: Sequence[Turn],
        persona: Persona = DOCUMENT_PERSONA,
    ) -> AsyncIterator[AnswerEvent]:
        picks = self.pick_sentences(question, chunks)
        if not picks:
            async for event in self._words(persona.not_found):
                yield event
            return
        citations = CitationBuilder()
        for i, (chunk, sentence) in enumerate(picks):
            async for event in self._words(sentence if i == 0 else f" {sentence}"):
                yield event
            yield citations.cite(chunk, sentence)

    def pick_sentences(self, question: str, chunks: Sequence[Chunk]) -> list[tuple[Chunk, str]]:
        """The sentence that best matches the question, plus a related neighbour.

        Sentences are scored by the rarity of the question terms they share. Terms in the
        section heading above a sentence add to its score, at a lower weight. Retrieval has already
        ranked the chunks, so this only chooses sentences inside them. The next sentence in
        the same section is added when it also matches; otherwise a second section that
        matches as well is used.
        """
        terms = set(tokenize(question))
        candidates = _candidates(chunks)
        if not terms or not candidates:
            return []
        df = Counter(t for c in candidates for t in c.terms | c.heading_terms)
        idf = {t: math.log(1 + len(candidates) / df[t]) for t in df}

        avg_len = sum(len(c.terms) for c in candidates) / len(candidates)

        def score(c: _Candidate) -> float:
            direct = sum(idf[t] for t in terms & c.terms)
            from_heading = sum(idf[t] for t in terms & c.heading_terms)
            # Long sentences match more terms by chance, so they are scaled down a little.
            length = 0.85 + 0.15 * len(c.terms) / avg_len
            lead = LEAD_BONUS if c.first_in_section else 1.0
            return lead * (direct + HEADING_WEIGHT * from_heading) / length

        scored = [(score(c), -i, c) for i, c in enumerate(candidates)]
        scored = [s for s in scored if s[0] > 0]
        if not scored:
            return []
        scored.sort(key=lambda s: (s[0], s[1]), reverse=True)
        best_score, _, best = scored[0]
        picks = [best]
        following = next((c for c in candidates if c.follows(best)), None)
        if following and terms & (following.terms | following.heading_terms):
            picks.append(following)
        else:
            for other_score, _, other in scored[1:]:
                if other_score >= best_score * 0.85 and other.heading != best.heading:
                    picks.append(other)
                    break
        return [(c.chunk, c.text) for c in picks[: self.max_sentences]]

    async def _words(self, text: str) -> AsyncIterator[TextEvent]:
        for piece in re.findall(r"\s*\S+", text):
            if self.delay:
                await asyncio.sleep(self.delay)
            yield TextEvent(text=piece)


HEADING_WEIGHT = 0.6  # a question term in the section heading
LEAD_BONUS = 1.1  # the first sentence of a section usually carries the main point


@dataclass(frozen=True)
class _Candidate:
    chunk: Chunk
    text: str
    heading: str
    position: int  # order within its chunk, for finding the next sentence
    first_in_section: bool
    terms: frozenset[str]
    heading_terms: frozenset[str]

    def follows(self, other: "_Candidate") -> bool:
        return (
            self.chunk is other.chunk
            and self.position == other.position + 1
            and self.heading == other.heading
        )


def _candidates(chunks: Sequence[Chunk]) -> list[_Candidate]:
    """Answer sentences with their section heading. Repeats from overlapping chunks are dropped."""
    out: list[_Candidate] = []
    seen: set[str] = set()
    for chunk in chunks:
        heading = ""
        first = False
        for pos, sentence in enumerate(split_sentences(chunk.text)):
            if not sentence.endswith(_END) and len(sentence.split()) <= 8:
                heading, first = sentence, True
                continue
            is_first, first = first, False
            if not _is_answer_sentence(sentence) or sentence in seen:
                continue
            seen.add(sentence)
            out.append(
                _Candidate(
                    chunk=chunk,
                    text=sentence,
                    heading=heading,
                    position=pos,
                    first_in_section=is_first,
                    terms=frozenset(tokenize(sentence)),
                    heading_terms=frozenset(tokenize(heading)),
                )
            )
    return out


_END = (".", "!", "?")


def _is_answer_sentence(sentence: str) -> bool:
    """Skip headings and page furniture; keep full sentences."""
    return (
        sentence.endswith((".", "!", "?"))
        and len(sentence.split()) >= 5
        and not _NOISE.match(sentence)
    )
