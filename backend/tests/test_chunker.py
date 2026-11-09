import pytest

from app.ingest.chunker import chunk_pages


def words(prefix: str, n: int) -> str:
    return " ".join(f"{prefix}{i}" for i in range(n))


def test_single_short_page_is_one_chunk():
    chunks = chunk_pages(["Hello there. Short page."], size=400, overlap=60)
    assert len(chunks) == 1
    c = chunks[0]
    assert (c.page_start, c.page_end) == (1, 1)
    assert c.text == "Hello there. Short page."
    assert c.chunk_id == "p1-c000"


def test_windows_have_expected_size_and_overlap():
    chunks = chunk_pages([words("w", 1000)], size=400, overlap=60)
    sizes = [len(c.text.split()) for c in chunks]
    assert sizes[0] == 400
    assert sum(sizes) - 60 * (len(chunks) - 1) == 1000
    # The last 60 words of one chunk start the next.
    assert chunks[0].text.split()[-60:] == chunks[1].text.split()[:60]


def test_page_ranges_follow_the_words():
    pages = [words("a", 300), words("b", 300), words("c", 300)]
    chunks = chunk_pages(pages, size=400, overlap=60)
    assert [(c.page_start, c.page_end) for c in chunks] == [(1, 2), (2, 3), (3, 3)]
    first = chunks[0]
    # Offsets map back to the right page.
    assert first.page_at(0) == 1
    assert first.page_at(first.text.index("b0")) == 2
    assert first.page_of("b10 b11 b12") == 2
    assert first.page_of("a5 a6") == 1


def test_page_of_ignores_whitespace_differences():
    chunks = chunk_pages(["Line one\nline two continues here."], size=50, overlap=5)
    assert chunks[0].page_of("one line   two") == 1


def test_chunk_ids_are_stable_and_unique():
    pages = [words("x", 900)]
    first = [c.chunk_id for c in chunk_pages(pages)]
    second = [c.chunk_id for c in chunk_pages(pages)]
    assert first == second
    assert len(set(first)) == len(first)


def test_empty_pages_are_skipped():
    chunks = chunk_pages(["", "only page two has text"], size=10, overlap=2)
    assert len(chunks) == 1
    assert chunks[0].page_start == 2


@pytest.mark.parametrize(("size", "overlap"), [(0, 0), (10, 10), (10, -1)])
def test_rejects_bad_parameters(size, overlap):
    with pytest.raises(ValueError):
        chunk_pages(["text"], size=size, overlap=overlap)


def test_help_center_chunks(sample_doc):
    assert sample_doc.pages == 9
    assert all(c.page_start <= c.page_end for c in sample_doc.chunks)
    assert sample_doc.chunks[0].page_start == 1
    assert sample_doc.chunks[-1].page_end == 9
