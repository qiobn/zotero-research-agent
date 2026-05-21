# Zotero Research Assistant

AI-powered research assistant built on top of your Zotero library. Provides 13 MCP tools for paper discovery, reading, citation, and library management — designed with zero functional overlap so LLMs always pick the right tool.

## Architecture

```
research_core/          # Shared Python library (80% of code)
├── zotero/             # pyzotero wrapper (hybrid: local read + web write)
├── parsers/            # PDF extraction + 800-char chunking with page tracking
├── rag/                # ChromaDB indexer/retriever, bge-m3 embedding, cross-encoder reranker
├── llm/                # LiteLLM wrapper
└── tools/              # 13 pure-function tools (search, read, cite, manage, admin)

project_a_mcp/          # MCP server for Cherry Studio / Claude Desktop / Cursor
project_b_agent/        # Full-stack agent app scaffold (FastAPI + Next.js, future)
```

## Key Features

- **Hybrid Search** — keyword (Zotero API) + semantic (ChromaDB) merged via Reciprocal Rank Fusion
- **Cross-Encoder Reranking** — optional `ms-marco-MiniLM-L-6-v2` re-scores retrieved chunks for higher precision
- **Chinese + English** — `BAAI/bge-m3` (1024-dim) natively supports multilingual queries
- **Page-Level Traceability** — every retrieved passage carries exact page numbers from the source PDF
- **Incremental Sync** — version-based diffing only re-indexes new or modified items
- **4-Level PDF Waterfall** — arXiv → Unpaywall → Semantic Scholar → PMC for open-access downloads
- **Dry-Run Safety** — all write operations preview changes before executing
- **Hybrid Zotero Mode** — local API for fast reads, web API for writes (when API key provided)

## Quick Start

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv .venv --python 3.13 && source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env   # edit as needed

# Index your Zotero library (requires Zotero 7 running)
python scripts/index_library.py

# Start the MCP server
zra-mcp
```

## MCP Tools (13 tools, 5 categories)

Tools are organized by **user intent**, not backend mechanism. They compose via `item_key`: discovery tools return keys, read/write tools consume them.

### DISCOVER — Find papers in your library

| Tool | When to use |
|---|---|
| `search_papers` | Find papers by topic, keywords, or filters. Combines keyword + semantic search with RRF fusion. Supports year range, tag include/exclude, and collection filters. |
| `find_similar_papers` | Given a specific paper (`item_key`), find conceptually similar papers in the library. Uses the source paper's title + abstract as the query. |
| `browse_library` | Navigate library structure: list collections, tags, recent additions, or items in a collection. Not for topic search. |
| `find_duplicates` | Scan the library for duplicate entries by normalized title or DOI match. Returns groups of 2+ items. |

### READ — Read paper content and annotations

| Tool | When to use |
|---|---|
| `get_paper` | Get metadata + abstract of one specific paper (title, authors, date, DOI, tags, collections). |
| `get_paper_content` | Read passages inside a paper. Three modes: semantic query within the paper, specific page number, or paper opening. Optionally includes user annotations. |
| `search_annotations` | Search highlights and comments across ALL papers by keyword. For finding "where did I annotate about X". |

### WRITE — Citations and paper import

| Tool | When to use |
|---|---|
| `suggest_citations` | Paste your draft text → get library papers that support your claims, with evidence text and page numbers. |
| `export_bibliography` | Export BibTeX or formatted citations for selected papers. |
| `add_paper` | Add a new paper by DOI, arXiv ID, or URL. Fetches metadata from CrossRef/arXiv, downloads open-access PDF via 4-level waterfall. **Dry-run by default.** |

### MANAGE — Organize your library

| Tool | When to use |
|---|---|
| `add_note` | Attach a reading note to a paper. **Dry-run by default** — previews before saving. |
| `edit_tags` | Add/remove tags on one or more papers in batch. **Dry-run by default.** |
| `manage_collections` | Create collections, add/remove papers from collections. **Dry-run by default.** |

### ADMIN — Index maintenance

| Tool | When to use |
|---|---|
| `sync_index` | Sync the vector index with your Zotero library. Incremental by default — only processes new/modified items using version tracking. Auto-detects embedding model changes. |

## Connect from Cherry Studio

```json
{
  "mcpServers": {
    "zra-mcp": {
      "name": "zra-mcp",
      "type": "stdio",
      "isActive": true,
      "command": "/path/to/project/.venv/bin/python",
      "args": ["-m", "project_a_mcp.server"],
      "env": {
        "CHROMA_PERSIST_DIR": "/path/to/project/.chroma_db",
        "EMBEDDING_MODEL": "BAAI/bge-m3"
      }
    }
  }
}
```

## Configuration

See [`.env.example`](./.env.example) for all available settings:

| Variable | Default | Description |
|---|---|---|
| `ZOTERO_LOCAL` | `true` | Use local Zotero API for reads |
| `ZOTERO_API_KEY` | — | Enables write operations via web API (hybrid mode) |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | Sentence-transformer model for semantic search |
| `RERANKER_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Cross-encoder for reranking. Set to `none` to disable |
| `CHROMA_PERSIST_DIR` | `.chroma_db` | ChromaDB storage directory |

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
