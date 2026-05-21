"""Zotero Research Assistant — MCP server.

Thirteen tools, one intent each, designed to compose via `item_key`.

Categories:
  DISCOVER   search_papers, find_similar_papers, browse_library, find_duplicates
  READ       get_paper, get_paper_content, search_annotations
  WRITE      suggest_citations, export_bibliography, add_paper
  MANAGE     add_note, edit_tags, manage_collections
  ADMIN      sync_index
"""

from __future__ import annotations

import os
from typing import Literal

from dotenv import load_dotenv
from fastmcp import FastMCP
from research_core.rag.indexer import Indexer
from research_core.rag.retriever import Retriever
from research_core.tools import (
    add_note as _add_note,
)
from research_core.tools import (
    add_paper as _add_paper,
)
from research_core.tools import (
    browse_library as _browse_library,
)
from research_core.tools import (
    edit_tags as _edit_tags,
)
from research_core.tools import (
    export_bibliography as _export_bibliography,
)
from research_core.tools import (
    find_duplicates as _find_duplicates,
)
from research_core.tools import (
    find_similar_papers as _find_similar_papers,
)
from research_core.tools import (
    get_paper as _get_paper,
)
from research_core.tools import (
    get_paper_content as _get_paper_content,
)
from research_core.tools import (
    manage_collections as _manage_collections,
)
from research_core.tools import (
    search_annotations as _search_annotations,
)
from research_core.tools import (
    search_papers as _search_papers,
)
from research_core.tools import (
    suggest_citations as _suggest_citations,
)
from research_core.tools import (
    sync_index as _sync_index,
)
from research_core.zotero.client import ZoteroClient

load_dotenv()

mcp = FastMCP(
    "Zotero Research Assistant",
    instructions=(
        "Help researchers discover, read, cite, and manage papers in their Zotero library. "
        "Tools compose via `item_key`: discovery tools return keys, read/write tools consume them. "
        "Prefer search_papers as the entry point. Never call multiple search tools for the same intent."
    ),
)

_zot: ZoteroClient | None = None
_retriever: Retriever | None = None
_indexer: Indexer | None = None


def _get_zot() -> ZoteroClient:
    global _zot
    if _zot is None:
        _zot = ZoteroClient(
            library_id=os.getenv("ZOTERO_LIBRARY_ID", "0"),
            library_type=os.getenv("ZOTERO_LIBRARY_TYPE", "user"),
            api_key=os.getenv("ZOTERO_API_KEY", ""),
            local=os.getenv("ZOTERO_LOCAL", "true").lower() == "true",
        )
    return _zot


def _get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever(persist_dir=os.getenv("CHROMA_PERSIST_DIR", ".chroma_db"))
    return _retriever


def _get_indexer() -> Indexer:
    global _indexer
    if _indexer is None:
        _indexer = Indexer(persist_dir=os.getenv("CHROMA_PERSIST_DIR", ".chroma_db"))
    return _indexer


# ╔══════════════════════════════════════════════════════════════╗
# ║  DISCOVER                                                    ║
# ╚══════════════════════════════════════════════════════════════╝


@mcp.tool()
def search_papers(
    query: str,
    year_from: int | None = None,
    year_to: int | None = None,
    tags_include: list[str] | None = None,
    tags_exclude: list[str] | None = None,
    collection_key: str = "",
    limit: int = 10,
) -> list[dict]:
    """Find papers in the user's Zotero library by topic, keywords, or filters.

    This is the PRIMARY discovery tool. Use it whenever the user wants to find papers
    they haven't yet picked out. Combines keyword matching against Zotero's library
    AND semantic similarity against the indexed PDF chunks, merged with Reciprocal
    Rank Fusion. The user does not need to specify which mechanism.

    When NOT to use:
    - User already gave you a paper key → use get_paper or get_paper_content instead.
    - User wants more papers like a specific one they named → use find_similar_papers.
    - User wants to browse collections/tags/recent additions → use browse_library.
    - User is writing a draft and wants citations for it → use suggest_citations.

    Args:
        query: Natural-language topic, concept, or keyword string.
        year_from/year_to: Publication year window (inclusive). Either or both optional.
        tags_include: Only return papers carrying ALL these tags.
        tags_exclude: Drop any paper carrying ANY of these tags.
        collection_key: Restrict search to a single Zotero collection.
        limit: Max results to return (default 10).

    Returns:
        List of papers ordered by relevance, each with key, title, authors, year,
        DOI, tags, score, source ('keyword' | 'semantic' | 'hybrid'),
        and the best matching passage with its page number when available.
    """
    hits = _search_papers(
        query=query,
        zot=_get_zot(),
        retriever=_get_retriever(),
        year_from=year_from,
        year_to=year_to,
        tags_include=tags_include,
        tags_exclude=tags_exclude,
        collection_key=collection_key,
        limit=limit,
    )
    return [h.__dict__ for h in hits]


@mcp.tool()
def find_similar_papers(item_key: str, limit: int = 10) -> list[dict]:
    """Find papers similar to a SPECIFIC paper the user has identified.

    Use this when the user says things like "find more papers like THIS one",
    "papers with the same methodology as X", or "what else is in my library
    related to this study". The input is the key of a known paper, NOT a query.

    When NOT to use:
    - User is searching by topic words → use search_papers.
    - User wants the contents of the source paper itself → use get_paper_content.

    Args:
        item_key: The Zotero item key of the source paper.
        limit: Max number of similar papers to return.

    Returns:
        Ranked list of similar papers, each with key, title, authors, year,
        relevance score, and a representative passage from each match.
    """
    hits = _find_similar_papers(item_key, _get_zot(), _get_retriever(), limit=limit)
    return [h.__dict__ for h in hits]


@mcp.tool()
def browse_library(
    scope: Literal["collections", "tags", "recent", "collection_items"],
    collection_key: str = "",
    limit: int = 20,
) -> dict:
    """Explore the STRUCTURE of the Zotero library (not its content).

    Use this for navigation, not for finding papers by topic. Choose `scope`:
      - "collections":      list all collections (folders) with their keys
      - "tags":             list all tags used in the library
      - "recent":           list recently added papers
      - "collection_items": list papers inside a specific collection (requires collection_key)

    When NOT to use:
    - User wants papers by topic or keyword → use search_papers.
    - User wants the metadata of one specific paper → use get_paper.

    Returns:
        {scope, items: [...], total}. Each item carries `key`, `name`/`tag`/`title` as
        appropriate for the scope.
    """
    res = _browse_library(scope, _get_zot(), collection_key=collection_key, limit=limit)
    return res.__dict__


@mcp.tool()
def find_duplicates() -> list[dict]:
    """Find duplicate papers in the library.

    Scans all items and groups them by normalized title or DOI match. Use this
    when the user wants to clean up their library or check for duplicate entries.

    When NOT to use:
    - User wants to find papers by topic → use search_papers.
    - User wants papers similar to one paper → use find_similar_papers.

    Returns:
        List of duplicate groups. Each group has `items` (list of papers with
        key, title, authors, year, doi) and `match_reason` ('doi_match' or 'title_match').
    """
    groups = _find_duplicates(_get_zot())
    return [g.__dict__ for g in groups]


# ╔══════════════════════════════════════════════════════════════╗
# ║  READ                                                        ║
# ╚══════════════════════════════════════════════════════════════╝


@mcp.tool()
def get_paper(item_key: str) -> dict:
    """Get metadata + abstract of ONE specific paper.

    Use this when the user has already identified a paper (via search_papers,
    find_similar_papers, browse_library, or by directly naming a key) and wants
    its bibliographic details: title, authors, date, abstract, DOI, tags, collections.

    When NOT to use:
    - User wants to read passages or specific content of the paper → use get_paper_content.
    - User wants formatted citation text → use export_bibliography.

    Args:
        item_key: The Zotero item key of the paper.

    Returns:
        Item dict with key, title, abstract, authors, date, doi, url, item_type,
        tags, collections, citation_key.
    """
    item = _get_paper(item_key, _get_zot())
    return item.model_dump()


@mcp.tool()
def get_paper_content(
    item_key: str,
    query: str = "",
    page: int | None = None,
    include_annotations: bool = False,
    limit: int = 5,
) -> dict:
    """Read content INSIDE a specific paper.

    Use this to read what a paper actually says. Three modes (mutually exclusive):
      1. `query` provided → returns the top passages semantically matching the query,
         restricted to this paper only. Best for "What does paper X say about Y?".
      2. `page` provided → returns all chunks that intersect that page number. Best
         for "What is on page N of paper X?".
      3. Neither → returns the first `limit` chunks (paper opening / intro).

    Set `include_annotations=True` to additionally return the user's OWN highlights
    and comments on this paper. Useful for "What did I highlight in this paper?".

    When NOT to use:
    - User wants to find papers across the library → use search_papers.
    - User wants metadata only (no body text) → use get_paper.
    - User wants to search annotations across ALL papers → use search_annotations.

    Args:
        item_key: The paper to read from. Required.
        query: Topic words to search for inside this paper (mode 1).
        page: Specific page number (mode 2).
        include_annotations: If True, also fetch user highlights/notes.
        limit: Max number of passages to return.

    Returns:
        {item_key, title, passages: [{text, page_start, page_end, score}],
         annotations: [{type, text, comment, page, color}] (if requested)}.
    """
    content = _get_paper_content(
        item_key=item_key,
        retriever=_get_retriever(),
        zot=_get_zot(),
        query=query,
        page=page,
        include_annotations=include_annotations,
        limit=limit,
    )
    return content.__dict__


@mcp.tool()
def search_annotations(query: str, limit: int = 20) -> list[dict]:
    """Search highlights and comments across ALL papers in the library.

    Use this when the user asks things like "where did I highlight gravity model",
    "find my notes about methodology", or "what did I annotate about X".

    When NOT to use:
    - User wants annotations from ONE specific paper → use get_paper_content with
      include_annotations=True.
    - User wants to find papers by topic → use search_papers.

    Args:
        query: Keyword or phrase to search within annotation text and comments.
        limit: Max results to return.

    Returns:
        List of matching annotations, each with item_key, title (of parent paper),
        annotation text, comment, page number, type, and color.
    """
    return _search_annotations(query, _get_zot(), limit=limit)


# ╔══════════════════════════════════════════════════════════════╗
# ║  WRITE                                                       ║
# ╚══════════════════════════════════════════════════════════════╝


@mcp.tool()
def suggest_citations(draft_text: str, top_k: int = 5) -> list[dict]:
    """For a passage from the USER'S OWN WRITING, suggest papers from their library
    that could be cited to support each claim.

    The input is text the user has WRITTEN (a paragraph of their draft), not a
    search query. Each suggestion includes the matching evidence text and page so
    the user can verify the citation is appropriate, plus authors and year so you
    can immediately render inline citations like (Smith, 2023).

    Workflow this fits:
        draft_text → suggest_citations → (user picks which to keep) → export_bibliography

    When NOT to use:
    - User just wants to find papers about a topic → use search_papers.
    - User asks "what does X say about Y" → use get_paper_content.

    Args:
        draft_text: The user's own paragraph or sentence (NOT a search query).
        top_k: Max number of papers to suggest (1 best chunk per paper).

    Returns:
        List of suggestions with item_key, title, authors, year, evidence_text,
        page, and relevance score.
    """
    suggestions = _suggest_citations(draft_text, _get_retriever(), _get_zot(), top_k=top_k)
    return [s.__dict__ for s in suggestions]


@mcp.tool()
def export_bibliography(
    item_keys: list[str],
    format: Literal["bibtex", "citation"] = "bibtex",
) -> dict:
    """Export formatted bibliography entries for a SET of papers.

    Use this when the user needs ready-to-paste citation text (typically BibTeX for
    LaTeX, or a plain author-year-title rendering for Word/Markdown). The papers
    must already be identified by their item keys.

    When NOT to use:
    - User hasn't picked which papers to cite yet → use suggest_citations first.
    - User wants metadata for inspection, not export → use get_paper.

    Args:
        item_keys: List of Zotero item keys to export.
        format: "bibtex" (default) or "citation" (plain "Authors (Year). Title.").

    Returns:
        {format, entries: {key: text}, combined_text: <all entries joined>}.
    """
    bib = _export_bibliography(item_keys, _get_zot(), fmt=format)
    return bib.__dict__


@mcp.tool()
def add_paper(
    identifier: str,
    collection_key: str = "",
    tags: list[str] | None = None,
    confirm: bool = False,
) -> dict:
    """Add a NEW paper to the Zotero library by DOI, arXiv ID, or URL.

    SAFETY: defaults to preview mode. First call fetches metadata and shows what
    would be created; only when called again with confirm=true does it actually
    create the item. Automatically tries to download the open-access PDF from
    Unpaywall and arXiv.

    Use this when the user says "add this paper", "import 10.xxxx/yyyy",
    "add this arXiv paper", or pastes a DOI/URL.

    When NOT to use:
    - Paper is already in the library → use search_papers to verify first.
    - User wants to read or cite an existing paper → use get_paper / suggest_citations.

    Args:
        identifier: DOI (e.g. "10.1234/abcd"), arXiv ID ("2301.00001"),
                    or URL (https://arxiv.org/abs/..., https://doi.org/...).
        collection_key: Optional collection to add the paper to.
        tags: Optional tags to apply to the new paper.
        confirm: Must be True to actually create. Default False = preview only.

    Returns:
        {success, item_key, title, doi, pdf_attached, metadata, error}.
    """
    res = _add_paper(
        identifier=identifier,
        zot=_get_zot(),
        collection_key=collection_key,
        tags=tags,
        confirm=confirm,
    )
    return res.__dict__


# ╔══════════════════════════════════════════════════════════════╗
# ║  MANAGE                                                      ║
# ╚══════════════════════════════════════════════════════════════╝


@mcp.tool()
def add_note(
    item_key: str,
    title: str,
    content: str,
    tags: list[str] | None = None,
    confirm: bool = False,
) -> dict:
    """Attach a NOTE to a paper in the Zotero library.

    SAFETY: defaults to dry-run. First call returns a preview of what would be
    created; only when called again with confirm=true does it actually save.

    Use this for capturing reading notes, summaries, key insights, or any text the
    user wants permanently attached to a paper.

    When NOT to use:
    - User wants to label papers for organization → use edit_tags.
    - User wants to organize papers into folders → use manage_collections.

    Args:
        item_key: Parent paper's key.
        title: Note heading (rendered as <h1>).
        content: Note body. May contain basic HTML.
        tags: Optional tags to attach to the note itself.
        confirm: Must be True to actually write. Default False = preview only.

    Returns:
        {confirmed, preview, result, error}. When confirmed=False, the response is
        a safe preview only.
    """
    res = _add_note(
        item_key=item_key,
        title=title,
        content=content,
        zot=_get_zot(),
        tags=tags,
        confirm=confirm,
    )
    return res.__dict__


@mcp.tool()
def edit_tags(
    item_keys: list[str],
    add: list[str] | None = None,
    remove: list[str] | None = None,
    confirm: bool = False,
) -> dict:
    """Add or remove TAGS on one or more papers.

    SAFETY: defaults to dry-run. First call returns a diff preview per paper
    (current tags, what will be added, what will be removed, resulting set). Call
    again with confirm=true to actually apply.

    Use this for organizing the library: bulk-categorizing papers, marking
    to-read/read, project labels, etc.

    When NOT to use:
    - User wants to write reading notes → use add_note.
    - User just wants to see which tags exist → use browse_library(scope='tags').

    Args:
        item_keys: Paper keys to operate on. Supports batch.
        add: Tags to add (no-op for papers that already have them).
        remove: Tags to remove (no-op for papers without them).
        confirm: Must be True to apply. Default False = preview only.

    Returns:
        {confirmed, preview: {action, add, remove, items: [diffs]}, result}.
    """
    res = _edit_tags(
        item_keys=item_keys,
        zot=_get_zot(),
        add=add,
        remove=remove,
        confirm=confirm,
    )
    return res.__dict__


@mcp.tool()
def manage_collections(
    action: Literal["create", "add_items", "remove_items"],
    name: str = "",
    parent_key: str = "",
    collection_key: str = "",
    item_keys: list[str] | None = None,
    confirm: bool = False,
) -> dict:
    """Create collections (folders) or add/remove papers from them.

    SAFETY: defaults to dry-run. First call shows a preview; call again with
    confirm=true to apply.

    Actions:
      - "create":       Create a new collection. Requires `name`, optional `parent_key`.
      - "add_items":    Add papers to an existing collection. Requires `collection_key`
                        and `item_keys`.
      - "remove_items": Remove papers from a collection. Requires `collection_key`
                        and `item_keys`.

    When NOT to use:
    - User wants to browse existing collections → use browse_library(scope='collections').
    - User wants to add/remove tags → use edit_tags.

    Args:
        action: One of "create", "add_items", "remove_items".
        name: Collection name (for "create").
        parent_key: Optional parent collection key (for "create" under a folder).
        collection_key: Collection key (for "add_items" / "remove_items").
        item_keys: Paper keys to add or remove (for "add_items" / "remove_items").
        confirm: Must be True to apply. Default False = preview only.

    Returns:
        {confirmed, preview, result, error}.
    """
    res = _manage_collections(
        action=action,
        zot=_get_zot(),
        name=name,
        parent_key=parent_key,
        collection_key=collection_key,
        item_keys=item_keys,
        confirm=confirm,
    )
    return res.__dict__


# ╔══════════════════════════════════════════════════════════════╗
# ║  ADMIN                                                       ║
# ╚══════════════════════════════════════════════════════════════╝


@mcp.tool()
def sync_index(force_rebuild: bool = False) -> dict:
    """Synchronize the vector index with the current Zotero library.

    Run this AFTER the user has added new PDFs to Zotero (otherwise the semantic
    side of search_papers will miss the new papers).

    **Incremental by default**: uses Zotero item version tracking to detect new,
    modified, and deleted items. Only changed items are re-parsed and re-indexed.
    If the embedding model has changed since the last sync, a full rebuild is
    triggered automatically.

    Set force_rebuild=True to wipe and reindex everything (slow; only use if
    chunking parameters changed or the index is suspected corrupt).

    Args:
        force_rebuild: Wipe and reindex from scratch. Default False (incremental).

    Returns:
        {added, updated, skipped, removed, failed, total_chunks_after, incremental}.
    """
    report = _sync_index(
        zot=_get_zot(),
        indexer=_get_indexer(),
        retriever=_get_retriever(),
        force_rebuild=force_rebuild,
    )
    return report.__dict__


def main():
    """Entry point for `zra-mcp` console script."""
    mcp.run()


if __name__ == "__main__":
    main()
