"""Retrieval for one question, including follow-ups and the no-answer threshold."""

import re
from collections.abc import Sequence
from dataclasses import dataclass

from app.models import ScoredChunk, Turn
from app.retrieval.base import Retriever

# Words that usually point back to the previous question ("what about managers?").
_FOLLOW_UP = re.compile(
    r"^(and|also|what about|how about|same for|what if)\b"
    r"|\b(it|its|that|this|they|them|those|these)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RetrievalResult:
    hits: list[ScoredChunk]
    answerable: bool
    query: str


def looks_like_follow_up(question: str) -> bool:
    return bool(_FOLLOW_UP.search(question.strip()))


def retrieve(
    retriever: Retriever,
    question: str,
    history: Sequence[Turn],
    *,
    k: int,
    min_score: float,
) -> RetrievalResult:
    """Search with the question; for follow-ups, add the previous question as context.

    If the best score is under `min_score`, the result is marked not answerable and the
    caller answers "not in this document" without calling a model.
    """
    query = question
    if history and looks_like_follow_up(question):
        query = f"{history[-1].question} {question}"
    hits = retriever.search(query, k)
    best = hits[0].score if hits else 0.0
    return RetrievalResult(hits=hits, answerable=best >= min_score, query=query)
