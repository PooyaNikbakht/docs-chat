"""Okapi BM25 over chunks. Small, dependency-free, and good enough for one document."""

import math
from collections import Counter
from collections.abc import Sequence

from app.models import Chunk, ScoredChunk
from app.retrieval.text import tokenize


class BM25Retriever:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self._chunks: list[Chunk] = []
        self._tfs: list[Counter[str]] = []
        self._lengths: list[int] = []
        self._idf: dict[str, float] = {}
        self._avg_len = 0.0

    def index(self, chunks: Sequence[Chunk]) -> None:
        self._chunks = list(chunks)
        self._tfs = [Counter(tokenize(c.text)) for c in self._chunks]
        self._lengths = [sum(tf.values()) for tf in self._tfs]
        n = len(self._chunks)
        self._avg_len = (sum(self._lengths) / n) if n else 0.0
        df: Counter[str] = Counter()
        for tf in self._tfs:
            df.update(tf.keys())
        self._idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}

    def search(self, query: str, k: int) -> list[ScoredChunk]:
        terms = set(tokenize(query))
        if not terms or not self._chunks:
            return []
        scored = [
            ScoredChunk(chunk=chunk, score=self._score(terms, i))
            for i, chunk in enumerate(self._chunks)
        ]
        scored = [s for s in scored if s.score > 0]
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:k]

    def _score(self, terms: set[str], i: int) -> float:
        tf, length = self._tfs[i], self._lengths[i]
        norm = self.k1 * (1 - self.b + self.b * length / (self._avg_len or 1))
        score = 0.0
        for term in terms:
            f = tf.get(term, 0)
            if f:
                score += self._idf[term] * f * (self.k1 + 1) / (f + norm)
        return score
