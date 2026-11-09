"""Domain types and API schemas."""

from bisect import bisect_right
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.retrieval.text import find_loose


@dataclass(frozen=True)
class Chunk:
    """A slice of the document. `page_marks` maps character offsets to pages."""

    chunk_id: str
    text: str
    page_start: int
    page_end: int
    # Sorted (char_offset, page) pairs: text from that offset onward is on that page.
    page_marks: tuple[tuple[int, int], ...] = ()

    def page_at(self, offset: int) -> int:
        """Page number for a character offset inside this chunk."""
        if not self.page_marks:
            return self.page_start
        offsets = [mark[0] for mark in self.page_marks]
        idx = bisect_right(offsets, max(offset, 0)) - 1
        return self.page_marks[max(idx, 0)][1]

    def page_of(self, quote: str) -> int:
        """Page where `quote` starts, falling back to the first page of the chunk."""
        span = find_loose(self.text, quote)
        return self.page_at(span[0]) if span else self.page_start


@dataclass
class Document:
    id: str
    name: str
    pages: int
    chunks: list[Chunk]
    created_at: float
    index: Any = field(default=None, repr=False)  # the Retriever, set after ingest
    suggestions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ScoredChunk:
    chunk: Chunk
    score: float


@dataclass(frozen=True)
class Turn:
    question: str
    answer: str


# ---- API schemas ----


class DocumentOut(BaseModel):
    id: str
    name: str
    pages: int
    chunks: int
    suggestions: list[str] = Field(description="Starter questions for this document")


class BookingAction(BaseModel):
    """A tap in the widget: a service, day or time chip, or a button on the confirm card."""

    type: Literal["service", "day", "slot", "confirm", "change"]
    id: str | None = Field(default=None, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    session_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    action: BookingAction | None = Field(
        default=None, description="Set when the visitor tapped a choice or a confirm button"
    )


class PageLink(BaseModel):
    page: int = Field(description="Help center page this link stands in for")
    label: str
    url: str


class BotOut(BaseModel):
    """Public widget config for one bot."""

    id: str
    name: str
    business: str
    subline: str
    greeting: str
    suggestions: list[str]
    accent_color: str
    handoff_text: str
    handoff_url: str
    tooltip: str | None
    source_label: str = Field(description='Label for source chips, as in "Help center, p. 3"')
    mode: Literal["live", "demo"] = Field(description="demo when answers come from mock mode")
    booking: bool = Field(default=False, description="True when the bot can check and book times")
    show_sources: bool = Field(default=False, description="True to show source chips under answers")
    page_links: list[PageLink] = Field(
        default_factory=list,
        description="Site pages to offer instead of source chips, keyed by help center page",
    )


class LimitsOut(BaseModel):
    max_upload_mb: int
    max_pages: int
    document_ttl_minutes: int | None


class HealthOut(BaseModel):
    status: Literal["ok"] = "ok"
    provider: Literal["anthropic", "openai", "mock"]
    model: str | None = None
    public_demo: bool = False
    limits: LimitsOut


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


# ---- Normalized answer events (what every provider adapter emits) ----


class TextEvent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class CitationEvent(BaseModel):
    type: Literal["citation"] = "citation"
    index: int
    chunk_id: str
    page: int
    quote: str
    context: str  # surrounding passage from the same page, for the citation panel


AnswerEvent = TextEvent | CitationEvent


# ---- Stream envelope events (added by the orchestrator) ----


class MetaEvent(BaseModel):
    """Sent first: which provider is answering, and why, if it is a fallback."""

    type: Literal["meta"] = "meta"
    provider: Literal["anthropic", "openai", "mock"]
    notice: str | None = None


class DoneEvent(BaseModel):
    type: Literal["done"] = "done"
    provider: Literal["anthropic", "openai", "mock"]
    grounded: bool
    citations: int
    # True when the answer isn't backed by the document, so the widget offers a human.
    handoff: bool = False


class ChoiceOption(BaseModel):
    id: str
    label: str
    detail: str | None = None


class ChoicesEvent(BaseModel):
    """Tappable choices under the answer. Slot choices only ever come from the booking tool."""

    type: Literal["choices"] = "choices"
    kind: Literal["service", "day", "slot"]
    label: str  # a short heading, also the accessible name of the group
    options: list[ChoiceOption]


class BookingEvent(BaseModel):
    """A booking summary: `pending` asks the visitor to confirm, `confirmed` is written."""

    type: Literal["booking"] = "booking"
    status: Literal["pending", "confirmed"]
    service: str
    when: str
    staff: str | None = None
    name: str
    contact: str
    price: str | None = None
    reference: str | None = None


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    code: str
    message: str


StreamEvent = (
    MetaEvent | TextEvent | CitationEvent | ChoicesEvent | BookingEvent | DoneEvent | ErrorEvent
)
