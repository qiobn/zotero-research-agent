"""Basic tests for the chunker module."""

from research_core.parsers.chunker import Chunk, chunk_text
from research_core.parsers.pdf import PageText


def test_chunk_text_basic():
    pages = [
        PageText(page_num=1, text="A" * 500),
        PageText(page_num=2, text="B" * 500),
    ]
    chunks = chunk_text(pages, chunk_size=400, overlap=50)
    assert len(chunks) > 0
    assert all(isinstance(c, Chunk) for c in chunks)
    assert chunks[0].page_start == 1


def test_chunk_text_empty():
    chunks = chunk_text([], chunk_size=400, overlap=50)
    assert chunks == []


def test_chunk_preserves_page_numbers():
    pages = [
        PageText(page_num=3, text="Hello world " * 100),
        PageText(page_num=4, text="Goodbye world " * 100),
    ]
    chunks = chunk_text(pages, chunk_size=200, overlap=30)
    page_nums = {c.page_start for c in chunks} | {c.page_end for c in chunks}
    assert 3 in page_nums or 4 in page_nums
