"""Turn uploaded bytes into an indexed, in-memory Document."""

import time
import uuid
from collections import Counter
from itertools import pairwise

from app.ingest.chunker import chunk_pages
from app.ingest.pdf import extract_pdf
from app.models import Document
from app.retrieval.bm25 import BM25Retriever
from app.settings import Settings


def suggest_questions(pages: list[str], limit: int = 3) -> list[str]:
    """Starter questions built from section headings: short lines followed by prose.

    Lines that repeat on several pages are running headers or footers and are skipped.
    """
    lines_by_page = [[ln.strip() for ln in p.splitlines() if ln.strip()] for p in pages]
    counts = Counter(line for lines in lines_by_page for line in set(lines))
    seen: set[str] = set()
    out: list[str] = []
    for lines in lines_by_page:
        for line, following in pairwise(lines):
            heading = line.lstrip("0123456789. ").strip()
            words = heading.split()
            if (
                counts[line] > 1
                or not 2 <= len(words) <= 6
                or heading.endswith(_PUNCT)
                or len(following.split()) < 8
                or heading.lower() in seen
            ):
                continue
            seen.add(heading.lower())
            topic = heading.removeprefix("About ").removeprefix("about ")
            first, *rest = topic.split()
            if first[1:].islower():
                first = first.lower()
            out.append(f"What does it say about {' '.join([first, *rest])}?")
            break  # one per page, so suggestions spread across the document
        if len(out) == limit:
            break
    return out


_PUNCT = (".", ",", ";", ":", "!", "?")


def ingest_pdf(
    name: str, data: bytes, settings: Settings, suggestions: list[str] | None = None
) -> Document:
    extracted = extract_pdf(
        data, max_pages=settings.max_pages, min_chars_per_page=settings.min_chars_per_page
    )
    chunks = chunk_pages(
        extracted.pages, size=settings.chunk_words, overlap=settings.chunk_overlap_words
    )
    retriever = BM25Retriever()
    retriever.index(chunks)
    return Document(
        id=uuid.uuid4().hex[:12],
        name=name,
        pages=len(extracted.pages),
        chunks=chunks,
        created_at=time.time(),
        index=retriever,
        suggestions=suggestions if suggestions is not None else suggest_questions(extracted.pages),
    )
