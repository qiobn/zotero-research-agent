"""Pure-function tool collection for MCP and agent use.

Each tool maps to a single user intent (not to a backend mechanism), and tools are
designed to compose via `item_key`.
"""

from research_core.tools.admin import SyncReport, sync_index
from research_core.tools.cite import (
    BibliographyExport,
    CitationSuggestion,
    export_bibliography,
    suggest_citations,
)
from research_core.tools.manage import (
    AddPaperResult,
    WriteResult,
    add_note,
    add_paper,
    edit_tags,
    manage_collections,
)
from research_core.tools.read import PaperContent, get_paper, get_paper_content, search_annotations
from research_core.tools.search import (
    BrowseResult,
    DuplicateGroup,
    PaperHit,
    browse_library,
    find_duplicates,
    find_similar_papers,
    search_papers,
)

__all__ = [
    "AddPaperResult",
    "BibliographyExport",
    "BrowseResult",
    "CitationSuggestion",
    "DuplicateGroup",
    "PaperContent",
    "PaperHit",
    "SyncReport",
    "WriteResult",
    "add_note",
    "add_paper",
    "browse_library",
    "edit_tags",
    "export_bibliography",
    "find_duplicates",
    "find_similar_papers",
    "get_paper",
    "get_paper_content",
    "manage_collections",
    "search_annotations",
    "search_papers",
    "suggest_citations",
    "sync_index",
]
