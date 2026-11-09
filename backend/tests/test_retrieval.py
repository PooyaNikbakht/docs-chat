from app.models import Chunk, Turn
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.query import looks_like_follow_up, retrieve
from app.retrieval.text import find_loose, split_sentences, tokenize


def make_chunks() -> list[Chunk]:
    texts = [
        "Employees get 15 days of paid time off each year.",
        "Expenses must be submitted within 30 days with receipts.",
        "Laptops are replaced every three years.",
    ]
    return [Chunk(f"c{i}", t, i + 1, i + 1) for i, t in enumerate(texts)]


def test_bm25_ranks_the_matching_chunk_first():
    r = BM25Retriever()
    r.index(make_chunks())
    hits = r.search("How many paid time off days?", k=6)
    assert hits[0].chunk.chunk_id == "c0"
    assert hits == sorted(hits, key=lambda h: h.score, reverse=True)


def test_bm25_returns_nothing_for_unknown_terms():
    r = BM25Retriever()
    r.index(make_chunks())
    assert r.search("capital of France", k=6) == []
    assert r.search("the and of", k=6) == []  # stopwords only


def test_bm25_respects_k():
    r = BM25Retriever()
    r.index(make_chunks())
    assert len(r.search("days years receipts", k=2)) == 2


def test_threshold_marks_off_topic_questions_unanswerable(sample_doc):
    on = retrieve(sample_doc.index, "Can I pause my subscription?", [], k=6, min_score=1.0)
    off = retrieve(sample_doc.index, "What is the capital of France?", [], k=6, min_score=1.0)
    weak = retrieve(sample_doc.index, "How do I bake bread for employees?", [], k=6, min_score=1.0)
    assert on.answerable and on.hits[0].score >= 1.0
    assert not off.answerable
    assert not weak.answerable


def test_follow_up_questions_use_the_previous_question(sample_doc):
    history = [Turn("Can I pause my subscription?", "Yes, for up to 3 months.")]
    result = retrieve(sample_doc.index, "Can I skip it instead?", history, k=6, min_score=1.0)
    assert result.query.startswith("Can I pause")
    assert result.answerable
    alone = retrieve(
        sample_doc.index, "What is the capital of France?", history, k=6, min_score=1.0
    )
    assert alone.query == "What is the capital of France?"
    assert not alone.answerable


def test_follow_up_detection():
    assert looks_like_follow_up("What about part-time staff?")
    assert looks_like_follow_up("Does that include holidays?")
    assert not looks_like_follow_up("How many sick days are there?")


def test_tokenize_stems_and_drops_stopwords():
    assert tokenize("How many PTO days do employees get?") == ["pto", "day", "employee"]


def test_split_sentences_handles_headings_and_abbreviations():
    text = "Paid Time Off\nNew staff at Northwind Co. get 15 days. PTO accrues\nmonthly."
    assert split_sentences(text) == [
        "Paid Time Off",
        "New staff at Northwind Co. get 15 days.",
        "PTO accrues monthly.",
    ]


def test_find_loose():
    assert find_loose("a  b\nc d", "b c") == (3, 6)
    assert find_loose("abc", "x") is None
    assert find_loose("abc", "  ") is None
