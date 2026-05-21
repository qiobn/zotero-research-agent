"""Reading tools — get paper metadata and content."""

from __future__ import annotations

from dataclasses import dataclass, field

from research_core.rag.retriever import Retriever
from research_core.zotero.client import ZoteroClient
from research_core.zotero.models import Annotation, Item


@dataclass
class PaperContent:
    """A paper-level reading result with passages and (optionally) user annotations."""

    item_key: str
    title: str
    passages: list[dict] = field(default_factory=list)
    annotations: list[dict] = field(default_factory=list)


def get_paper(item_key: str, zot: ZoteroClient) -> Item:
    """Return full metadata for one paper."""
    return zot.get_item(item_key)


def get_paper_content(
    item_key: str,
    retriever: Retriever,
    zot: ZoteroClient,
    query: str = "",
    page: int | None = None,
    include_annotations: bool = False,
    limit: int = 5,
) -> PaperContent:
    """Read content inside one paper.

    Mode selection:
    - query given → semantic search within this paper, return top-N passages
    - page given → return all chunks intersecting that page
    - neither → return the first `limit` chunks (paper opening)
    """
    title = ""
    try:
        title = zot.get_item(item_key).title
    except Exception:
        pass

    passages: list[dict] = []
    if query.strip():
        results = retriever.search_within_item(item_key, query, n_results=limit)
    elif page is not None:
        results = retriever.get_item_chunks(item_key, page=page)
    else:
        all_chunks = retriever.get_item_chunks(item_key)
        results = all_chunks[:limit]

    for r in results:
        passages.append(
            {
                "text": r.text,
                "page_start": r.page_start,
                "page_end": r.page_end,
                "score": round(r.score, 3) if r.score else None,
            }
        )

    annotations: list[dict] = []
    if include_annotations:
        anns: list[Annotation] = zot.get_annotations(item_key)
        for a in anns:
            annotations.append(
                {
                    "type": a.annotation_type,
                    "text": a.text,
                    "comment": a.comment,
                    "page": a.page,
                    "color": a.color,
                }
            )

    return PaperContent(
        item_key=item_key,
        title=title,
        passages=passages,
        annotations=annotations,
    )


def search_annotations(
    query: str,
    zot: ZoteroClient,
    limit: int = 20,
) -> list[dict]:
    """Search annotations (highlights, comments) across ALL papers in the library.

    Returns matching annotations with their parent paper info and page numbers.
    """
    return zot.search_all_annotations(query, limit=limit)
