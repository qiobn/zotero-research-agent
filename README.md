# Zotero Research Assistant

AI-powered research assistant built on top of your Zotero library.

- **`research_core`** — Shared Python library: Zotero integration, PDF parsing, RAG pipeline, LLM abstraction, tool collection
- **`project_a_mcp`** — MCP server for lab use (Cherry Studio / Claude Desktop / Cursor)
- **`project_b_agent`** — Full-stack agent app (FastAPI + Next.js) for personal use and portfolio

## Quick Start

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv .venv --python 3.13 && source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env

python scripts/index_library.py
zra-mcp
```

## Project A — MCP tools (9, zero overlap)

Tools are organized by **user intent** (not backend mechanism). LLM clients pick exactly one tool per intent.

| Category | Tool | When to use |
|---|---|---|
| Discover | `search_papers` | Find papers by topic / keyword / filter (hybrid keyword + semantic, RRF-merged) |
| Discover | `find_similar_papers` | "Find more papers like this one" — input is an `item_key`, not a query |
| Discover | `browse_library` | Navigate library structure (collections / tags / recent / collection items) |
| Read | `get_paper` | Metadata + abstract of one specific paper |
| Read | `get_paper_content` | Passages from inside a paper (query / page mode), optional annotations |
| Write | `suggest_citations` | Find references for the user's draft text (one suggestion per paper) |
| Write | `export_bibliography` | BibTeX or formatted citation text for selected papers |
| Manage | `add_note` | Attach a note to a paper (dry-run by default) |
| Manage | `edit_tags` | Add/remove tags in batch (dry-run by default) |
| Admin | `sync_index` | Sync the vector index with the current Zotero library |

### Connect from Cherry Studio / Claude Desktop

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

See [DEVELOPMENT.md](./DEVELOPMENT.md) for the full development roadmap.
