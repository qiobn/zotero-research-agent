"""Document parsing and chunking with page-level metadata."""

from research_core.parsers.chunker import Chunk, chunk_text
from research_core.parsers.pdf import extract_pdf_text

__all__ = ["extract_pdf_text", "chunk_text", "Chunk"]
