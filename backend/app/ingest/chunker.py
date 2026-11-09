"""Split page texts into overlapping word windows that remember their pages."""

import re
from dataclasses import dataclass

from app.models import Chunk

_WORD = re.compile(r"\S+")
_SPACES = re.compile(r"[ \t\f\v]+")


@dataclass(frozen=True)
class _Word:
    page: int
    start: int
    end: int


def chunk_pages(pages: list[str], *, size: int = 400, overlap: int = 60) -> list[Chunk]:
    """Chunk the document into windows of about `size` words with `overlap` words shared.

    Pages are 1-based. Each chunk keeps the page range it covers and a map from
    character offsets to pages, so a quote inside the chunk can be traced to its page.
    """
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("size must be positive and overlap must be in [0, size)")

    cleaned = [_SPACES.sub(" ", p.replace("\r", "")) for p in pages]
    words = [
        _Word(page=n, start=m.start(), end=m.end())
        for n, text in enumerate(cleaned, start=1)
        for m in _WORD.finditer(text)
    ]

    chunks: list[Chunk] = []
    step = size - overlap
    start = 0
    while start < len(words):
        window = words[start : start + size]
        chunks.append(_build_chunk(len(chunks), window, cleaned))
        if start + size >= len(words):
            break
        start += step
    return chunks


def _build_chunk(idx: int, window: list[_Word], pages: list[str]) -> Chunk:
    parts: list[str] = []
    marks: list[tuple[int, int]] = []
    offset = 0
    group_start = 0
    for i in range(1, len(window) + 1):
        if i == len(window) or window[i].page != window[group_start].page:
            first, last = window[group_start], window[i - 1]
            if parts:
                parts.append("\n\n")
                offset += 2
            marks.append((offset, first.page))
            piece = pages[first.page - 1][first.start : last.end]
            parts.append(piece)
            offset += len(piece)
            group_start = i
    page_start, page_end = window[0].page, window[-1].page
    return Chunk(
        chunk_id=f"p{page_start}-c{idx:03d}",
        text="".join(parts),
        page_start=page_start,
        page_end=page_end,
        page_marks=tuple(marks),
    )
