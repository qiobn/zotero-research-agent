"""Citation tools — suggest references for a draft, export formatted bibliography."""

from __future__ import annotations

import re
from dataclasses import dataclass

from research_core.rag.reranker import get_reranker
from research_core.rag.retriever import RetrievalResult, Retriever
from research_core.zotero.client import ZoteroClient

_SENTENCE_RE = re.compile(r"(?<=[.!?。！？])\s+")


@dataclass
class CitationSuggestion:
    item_key: str
    title: str
    authors: list[str]
    year: int
    evidence_text: str
    page: int
    relevance: float


@dataclass
class BibliographyExport:
    format: str
    entries: dict[str, str]
    combined_text: str


def _search_single(
    text: str, retriever: Retriever, n_results: int,
) -> list[RetrievalResult]:
    """Run a single retrieval + optional rerank pass."""
    raw = retriever.search(text, n_results=n_results)
    reranker = get_reranker()
    if reranker and raw:
        docs = [r.text for r in raw]
        reranked = reranker.rerank(text, docs, top_k=max(n_results // 2, 10))
        raw = [raw[idx] for idx, _ in reranked]
    return raw


def suggest_citations(
    draft_text: str,
    retriever: Retriever,
    zot: ZoteroClient,
    top_k: int = 5,
) -> list[CitationSuggestion]:
    """For a passage of the user's writing, find library papers that support the claims.

    Multi-sentence drafts are split into individual claims, each searched
    independently, then results are merged to produce more diverse citations.
    Returns at most one suggestion per paper (best matching chunk).
    """
    sentences = [s.strip() for s in _SENTENCE_RE.split(draft_text) if s.strip()]
    if len(sentences) <= 1:
        sentences = [draft_text]

    best_per_paper: dict[str, RetrievalResult] = {}

    if len(sentences) == 1:
        for r in _search_single(draft_text, retriever, max(top_k * 20, 100)):
            existing = best_per_paper.get(r.item_key)
            if existing is None or r.score > existing.score:
                best_per_paper[r.item_key] = r
    else:
        per_sentence = max(top_k * 6, 30)
        for sentence in sentences:
            if len(sentence) < 10:
                continue
            for r in _search_single(sentence, retriever, per_sentence):
                existing = best_per_paper.get(r.item_key)
                if existing is None or r.score > existing.score:
                    best_per_paper[r.item_key] = r

    ordered = sorted(best_per_paper.values(), key=lambda r: r.score, reverse=True)[:top_k]

    items = zot.get_items_batch([r.item_key for r in ordered])
    items_by_key = {it.key: it for it in items}

    suggestions: list[CitationSuggestion] = []
    for r in ordered:
        item = items_by_key.get(r.item_key)
        authors = item.authors if item else []
        year = ZoteroClient.parse_year(item.date) if item else 0
        title = item.title if item else r.title
        suggestions.append(
            CitationSuggestion(
                item_key=r.item_key,
                title=title,
                authors=authors,
                year=year,
                evidence_text=r.text[:300],
                page=r.page_start,
                relevance=round(r.score, 3),
            )
        )
    return suggestions


def export_bibliography(
    item_keys: list[str],
    zot: ZoteroClient,
    fmt: str = "bibtex",
) -> BibliographyExport:
    """Export formatted citation entries for the given papers.

    Currently supported formats: 'bibtex'. Other styles fall back to a plain
    'authors (year). title.' rendering.
    """
    if fmt == "bibtex":
        entries = zot.get_bibtex(item_keys)
        combined = "\n\n".join(v for v in entries.values() if v)
        return BibliographyExport(format=fmt, entries=entries, combined_text=combined)

    items = zot.get_items_batch(item_keys)
    entries = {}
    parts: list[str] = []
    for item in items:
        authors = ", ".join(item.authors) if item.authors else "Anon."
        year = ZoteroClient.parse_year(item.date)
        line = f"{authors} ({year}). {item.title}."
        if item.doi:
            line += f" doi:{item.doi}"
        entries[item.key] = line
        parts.append(line)
    return BibliographyExport(format=fmt, entries=entries, combined_text="\n".join(parts))
