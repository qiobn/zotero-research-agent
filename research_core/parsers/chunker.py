"""Text chunking with overlap and page-number preservation."""

from __future__ import annotations

from dataclasses import dataclass, field

from research_core.parsers.pdf import PageText


@dataclass
class Chunk:
    text: str
    page_start: int
    page_end: int
    chunk_idx: int
    metadata: dict = field(default_factory=dict)


def chunk_text(
    pages: list[PageText],
    chunk_size: int = 800,
    overlap: int = 120,
) -> list[Chunk]:
    """Split page-level text into overlapping chunks, preserving page numbers."""
    full_text = ""
    page_boundaries: list[tuple[int, int, int]] = []  # (start_char, end_char, page_num)
    for pt in pages:
        start = len(full_text)
        full_text += pt.text + "\n"
        page_boundaries.append((start, len(full_text), pt.page_num))

    if not full_text.strip():
        return []

    chunks: list[Chunk] = []
    idx = 0
    pos = 0
    while pos < len(full_text):
        end = min(pos + chunk_size, len(full_text))
        chunk_text_str = full_text[pos:end]
        if not chunk_text_str.strip():
            break
        page_start = _page_at(pos, page_boundaries)
        page_end = _page_at(end - 1, page_boundaries)
        chunks.append(Chunk(
            text=chunk_text_str.strip(),
            page_start=page_start,
            page_end=page_end,
            chunk_idx=idx,
        ))
        idx += 1
        pos = end - overlap if end < len(full_text) else end

    return chunks


def _page_at(char_pos: int, boundaries: list[tuple[int, int, int]]) -> int:
    for start, end, page_num in boundaries:
        if start <= char_pos < end:
            return page_num
    return boundaries[-1][2] if boundaries else 0
