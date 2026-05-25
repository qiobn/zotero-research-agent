"""Shared utilities for input normalization and safety."""

from __future__ import annotations

import html
import json


def normalize_list(value: object, field_name: str = "value") -> list[str]:
    """Coerce various LLM wire formats into a clean list[str].

    Accepted inputs:
        None                → []
        ["a", "b"]          → ["a", "b"]
        '["a","b"]'         → ["a", "b"]  (JSON string)
        "a, b, c"           → ["a", "b", "c"]  (comma-separated)
        "a"                 → ["a"]  (single string)
        [{"tag": "x"}, …]  → ["x", …]  (Zotero tag dicts)

    Raises ValueError on unparseable JSON or unexpected types.
    """
    if value is None:
        return []
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        if value.startswith("["):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError as e:
                raise ValueError(f"{field_name}: invalid JSON list — {e}") from e
            if not isinstance(parsed, list):
                raise ValueError(f"{field_name}: JSON parsed to {type(parsed).__name__}, expected list")
            return _flatten_items(parsed, field_name)
        if "," in value:
            return [s.strip() for s in value.split(",") if s.strip()]
        return [value]
    if isinstance(value, list):
        return _flatten_items(value, field_name)
    raise ValueError(f"{field_name}: expected list or string, got {type(value).__name__}")


def _flatten_items(items: list, field_name: str) -> list[str]:
    """Handle both plain strings and Zotero-style {"tag": "..."} dicts."""
    out: list[str] = []
    for item in items:
        if isinstance(item, str):
            s = item.strip()
            if s:
                out.append(s)
        elif isinstance(item, dict):
            tag = item.get("tag") or item.get("name") or item.get("value")
            if tag:
                out.append(str(tag).strip())
        else:
            out.append(str(item))
    return out


def escape_html(text: str) -> str:
    """Escape HTML special characters for safe embedding in Zotero note HTML."""
    return html.escape(text, quote=False)
