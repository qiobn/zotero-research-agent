"""PDF text extraction with per-page tracking."""

from __future__ import annotations

from dataclasses import dataclass

import pymupdf


@dataclass
class PageText:
    page_num: int
    text: str


def extract_pdf_text(path: str) -> list[PageText]:
    """Extract text from each page of a PDF. Returns list of (page_num, text)."""
    pages: list[PageText] = []
    with pymupdf.open(path) as doc:
        for i, page in enumerate(doc):
            text = page.get_text("text")
            if text.strip():
                pages.append(PageText(page_num=i + 1, text=text))
    return pages
