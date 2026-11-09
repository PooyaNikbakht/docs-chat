"""The retriever interface. BM25 is the default; embeddings or pgvector can implement it too."""

from collections.abc import Sequence
from typing import Protocol

from app.models import Chunk, ScoredChunk


class Retriever(Protocol):
    def index(self, chunks: Sequence[Chunk]) -> None:
        """Build the index for one document's chunks."""
        ...

    def search(self, query: str, k: int) -> list[ScoredChunk]:
        """Return up to k chunks, best first, with scores."""
        ...
