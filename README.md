# Zotero Research Assistant

AI-powered research assistant that turns your Zotero library into a conversational knowledge base. Provides **16 MCP tools** for paper discovery, reading, citation, annotation, and library management — designed with zero functional overlap so LLMs always pick the right tool.

Built for researchers who want to ask questions like *"find me papers about urban public services after 2022"*, *"what does this paper say about gravity models?"*, or *"help me cite this paragraph"* — and get precise, traceable answers grounded in their own library.

## Architecture

```
research_core/              # Shared Python library (core logic)
├── zotero/                 # pyzotero wrapper (hybrid: local read + web write)
├── parsers/                # PDF extraction + 800-char chunking with page tracking
├── rag/                    # ChromaDB indexer/retriever, bge-m3 embedding,
│                           # cross-encoder reranker, incremental sync
├── llm/                    # LiteLLM wrapper
├── tools/                  # 16 pure-function tools (search, read, cite, manage, admin)
└── utils.py                # Input normalization, HTML escaping

project_a_mcp/              # MCP server for Cherry Studio / Claude Desktop / Cursor
project_b_agent/            # Full-stack agent app scaffold (FastAPI + Next.js, planned)
```

## Key Features

- **Hybrid Search** — keyword (Zotero API) + semantic (ChromaDB) merged via Reciprocal Rank Fusion, with automatic fallback to Zotero full-text index
- **Cross-Encoder Reranking** — optional `ms-marco-MiniLM-L-6-v2` re-scores retrieved chunks for higher precision
- **Chinese + English** — `BAAI/bge-m3` (1024-dim) natively supports 100+ languages
- **Page-Level Traceability** — every retrieved passage carries exact page numbers from the source PDF
- **Full-Text & Outline** — read complete paper text or extract PDF table of contents on demand
- **Incremental Sync** — version-based diffing only re-indexes new or modified items; auto-sync on server startup
- **5-Format Paper Import** — add papers by DOI, arXiv ID, ISBN, BibTeX string, or URL
- **4-Level PDF Waterfall** — arXiv → Unpaywall → Semantic Scholar → PMC for open-access downloads
- **Duplicate Management** — find duplicates by title/DOI, then merge (tags, collections, children) with dry-run preview
- **Annotation CRUD** — search annotations across all papers; create highlight annotations on PDFs
- **Dry-Run Safety** — all write operations preview changes before executing
- **Hybrid Zotero Mode** — local API for fast reads, web API for writes (when API key provided)
- **API Concurrency Protection** — thread-safe RLock on all Zotero API calls
- **LLM Input Normalization** — tolerates JSON strings, comma-separated values, Zotero tag dicts, and other wire format variations
- **Global Error Handling** — structured `{error, tool}` responses instead of raw tracebacks

## Quick Start

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup environment
uv venv .venv --python 3.13 && source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env   # edit as needed

# Index your Zotero library (requires Zotero 7 running)
python scripts/index_library.py

# Start the MCP server
zra-mcp
```

## MCP Tools (16 tools, 5 categories)

Tools are organized by **user intent**, not backend mechanism. They compose via `item_key`: discovery tools return keys, read/write tools consume them.

### DISCOVER — Find and deduplicate papers

| Tool | Description |
|---|---|
| `search_papers` | **Primary entry point.** Hybrid keyword + semantic search with RRF fusion. Supports year range, tag include/exclude, collection filters. Falls back to Zotero full-text index when no results. |
| `find_similar_papers` | Given a specific paper, find conceptually similar ones using title + abstract as the query. Cross-encoder reranking for precision. |
| `browse_library` | Navigate library structure: list collections (with parent hierarchy), tags, recent additions, or items in a collection. |
| `find_duplicates` | Scan the library for duplicate entries by normalized title or DOI match. Returns groups of 2+ items. |
| `merge_duplicates` | **NEW.** Merge duplicate items into a keeper: combines tags, collections, re-parents children, deduplicates attachments, and trashes duplicates. Dry-run by default. |

### READ — Read content and annotations

| Tool | Description |
|---|---|
| `get_paper` | Metadata + abstract of one specific paper. |
| `get_paper_content` | Read inside a paper. Five modes: **fulltext** (complete text, up to 50 pages), **outline** (PDF table of contents), **query** (semantic search within the paper), **page** (specific page), or **default** (paper opening). Optionally includes annotations. |
| `search_annotations` | Search highlights and comments across ALL papers by keyword. Paginates through the entire library (no cap). |
| `create_annotation` | **NEW.** Create a highlight annotation on a paper's PDF. Auto-resolves parent item to PDF attachment. Dry-run by default. |

### WRITE — Citations and paper import

| Tool | Description |
|---|---|
| `suggest_citations` | Paste your draft text → get library papers that support your claims. Multi-sentence drafts are split and searched independently for diverse results. |
| `export_bibliography` | Export BibTeX or formatted citations for selected papers. |
| `add_paper` | Add a new paper by **DOI, arXiv ID, ISBN, BibTeX string, or URL**. Fetches metadata from CrossRef/arXiv/OpenLibrary. Downloads open-access PDF via 4-level waterfall. Dry-run by default. |

### MANAGE — Organize your library

| Tool | Description |
|---|---|
| `add_note` | Attach a reading note to a paper with HTML title escaping. Dry-run by default. |
| `edit_tags` | Add/remove tags on one or more papers in batch. Dry-run by default. |
| `manage_collections` | Create collections, add/remove papers from collections. Dry-run by default. |

### ADMIN — Index maintenance

| Tool | Description |
|---|---|
| `sync_index` | Sync the vector index with your Zotero library. Incremental by default — only processes new/modified items using version tracking. Auto-detects embedding model changes. Also runs automatically on server startup (disable with `ZRA_AUTO_SYNC=false`). |

## Connect from Cherry Studio

```json
{
  "mcpServers": {
    "zra-mcp": {
      "command": "/path/to/project/.venv/bin/python",
      "args": ["-m", "project_a_mcp.server"],
      "cwd": "/path/to/project"
    }
  }
}
```

See [`docs/cherry-studio-setup.md`](./docs/cherry-studio-setup.md) for a detailed configuration guide (in Chinese).

## Configuration

See [`.env.example`](./.env.example) for all available settings:

| Variable | Default | Description |
|---|---|---|
| `ZOTERO_LOCAL` | `true` | Use local Zotero API for reads |
| `ZOTERO_API_KEY` | — | Enables write operations via web API (hybrid mode) |
| `ZOTERO_LIBRARY_ID` | `0` | Your Zotero user/group library ID |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | Sentence-transformer model for semantic search |
| `RERANKER_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Cross-encoder for reranking (`none` to disable) |
| `CHROMA_PERSIST_DIR` | `.chroma_db` | ChromaDB storage directory |
| `ZRA_AUTO_SYNC` | `true` | Auto-sync index on server startup |

## Development

```bash
# Run tests (requires Zotero running)
pytest tests/ -v

# Lint
ruff check .
```

See [DEVELOPMENT.md](./DEVELOPMENT.md) for the full roadmap.

## License

MIT
