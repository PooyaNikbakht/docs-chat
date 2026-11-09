"""Small text utilities shared by retrieval and the answer adapters."""

import re
import unicodedata

_TOKEN = re.compile(r"[a-z0-9]+")

_STOPWORD_TEXT = """
a about above after again all also am an and any are as at be because been before being
below between both but by can could did do does doing done down during each few for from
further get gets got had has have having he her here hers him his how i if in into is it
its itself just me more most my no nor not now of off on once only or other our ours out
over own same she should so some such than that the their theirs them then there these
they this those through to too under until up very was we were what when where which while
who whom why will with would you your yours tell please much many dont doesnt s t
"""
STOPWORDS = frozenset(_STOPWORD_TEXT.split())


def stem(word: str) -> str:
    """A deliberately light stemmer: plurals and a few common suffixes."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 5 and word.endswith("ing"):
        return word[:-3]
    if len(word) > 4 and word.endswith("ed") and not word.endswith("eed"):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def tokenize(text: str) -> list[str]:
    """Lowercase, fold accents (café to cafe), split on non-alphanumerics, drop stopwords, stem."""
    text = text.lower().replace("'", "").replace("\u2019", "")
    if not text.isascii():
        text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return [stem(t) for t in _TOKEN.findall(text) if t not in STOPWORDS]


_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"(])")


def split_sentences(text: str) -> list[str]:
    """Split text into sentences. Short lines without end punctuation count as headings."""
    blocks: list[tuple[str, bool]] = []  # (text, is_heading)
    current: list[str] = []

    def flush() -> None:
        if current:
            blocks.append((" ".join(current), False))
            current.clear()

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            flush()
            continue
        if len(line.split()) <= 8 and not line.endswith(_END_PUNCT):
            flush()
            blocks.append((line, True))
            continue
        current.append(line)
    flush()

    sentences: list[str] = []
    for block, is_heading in blocks:
        if is_heading:
            sentences.append(block)
            continue
        pieces = [s.strip() for s in _SENTENCE_END.split(block) if s.strip()]
        merged: list[str] = []
        for piece in pieces:
            if merged and _ends_with_abbreviation(merged[-1]):
                merged[-1] = f"{merged[-1]} {piece}"
            else:
                merged.append(piece)
        sentences.extend(merged)
    return sentences


_END_PUNCT = (".", ",", ";", ":", "!", "?")
_ABBREVIATIONS = frozenset(
    {"co.", "inc.", "ltd.", "e.g.", "i.e.", "dr.", "mr.", "ms.", "no.", "st."}
)


def _ends_with_abbreviation(sentence: str) -> bool:
    last = sentence.rsplit(" ", 1)[-1].lower()
    return last in _ABBREVIATIONS or bool(re.fullmatch(r"\d+\.", last))


def find_loose(haystack: str, needle: str) -> tuple[int, int] | None:
    """Find `needle` in `haystack`, ignoring differences in whitespace. Returns (start, end)."""
    words = needle.split()
    if not words:
        return None
    pattern = r"\s+".join(re.escape(w) for w in words)
    match = re.search(pattern, haystack)
    return (match.start(), match.end()) if match else None
