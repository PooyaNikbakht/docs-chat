from app.models import CitationEvent, TextEvent
from app.providers.base import NOT_IN_DOC_MESSAGE, CitationBuilder, best_quote, context_for
from app.providers.mock import MockProvider


async def run(provider, question, chunks):
    return [e async for e in provider.stream_answer(question, chunks, [])]


async def test_mock_is_deterministic(sample_doc):
    chunks = [h.chunk for h in sample_doc.index.search("How long does shipping take?", 6)]
    first = await run(MockProvider(), "How long does shipping take?", chunks)
    second = await run(MockProvider(), "How long does shipping take?", chunks)
    assert first == second


async def test_mock_says_not_in_document_when_nothing_matches(sample_doc):
    events = await run(MockProvider(), "zebra quantum", sample_doc.chunks)
    assert "".join(e.text for e in events if isinstance(e, TextEvent)) == NOT_IN_DOC_MESSAGE
    assert not any(isinstance(e, CitationEvent) for e in events)


def test_citation_builder_reuses_numbers(sample_doc):
    chunk = sample_doc.chunks[0]
    builder = CitationBuilder()
    ships = "We ship to Canada and the United States, including every US state."
    a = builder.cite(chunk, ships)
    b = builder.cite(chunk, "Please include your order number if your question is about an order.")
    again = builder.cite(chunk, ships.replace(" and ", "   and "))
    assert (a.index, b.index, again.index) == (1, 2, 1)
    assert a.page == 2
    assert builder.count == 2


def test_best_quote_and_context(sample_doc):
    chunk = sample_doc.chunks[0]
    quote = best_quote(chunk, "include your order number")
    assert quote == "Please include your order number if your question is about an order."
    ctx = context_for(chunk, quote)
    assert quote in ctx
    assert "Getting help from a person" not in ctx  # headings left out
