"""Admin tools — index maintenance with incremental sync."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from loguru import logger

from research_core.parsers.chunker import chunk_text
from research_core.parsers.pdf import extract_pdf_text
from research_core.rag.indexer import Indexer
from research_core.rag.retriever import Retriever
from research_core.rag.sync_state import SyncState
from research_core.zotero.client import ZoteroClient


@dataclass
class SyncReport:
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    failed: list[dict] = field(default_factory=list)
    total_chunks_after: int = 0
    incremental: bool = True


def sync_index(
    zot: ZoteroClient,
    indexer: Indexer,
    retriever: Retriever,
    force_rebuild: bool = False,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> SyncReport:
    """Synchronize the vector index with the Zotero library.

    Incremental by default: uses Zotero item versions to detect new, modified,
    and deleted items. Only changed items are re-parsed and re-indexed.

    force_rebuild=True drops ALL stored state and reindexes everything.
    """
    report = SyncReport(incremental=not force_rebuild)
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", ".chroma_db")
    embedding_model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")

    state = SyncState.load(persist_dir)

    if state.embedding_model and state.embedding_model != embedding_model:
        logger.warning(
            f"Embedding model changed ({state.embedding_model} → {embedding_model}), "
            "forcing full rebuild"
        )
        force_rebuild = True
        report.incremental = False

    if force_rebuild:
        indexed_keys = retriever.list_indexed_items()
        for key in indexed_keys:
            indexer.delete_item(key)
            report.removed.append(key)
        state.item_versions.clear()

    current_versions = zot.get_item_versions()
    new_keys, modified_keys, deleted_keys = state.diff(current_versions)

    for key in deleted_keys:
        indexer.delete_item(key)
        report.removed.append(key)
        state.item_versions.pop(key, None)

    keys_to_process = new_keys | modified_keys
    if not keys_to_process:
        logger.info("No new or modified items to index")
        report.total_chunks_after = indexer.count()
        state.embedding_model = embedding_model
        state.save()
        for key in current_versions:
            if key not in keys_to_process and key not in deleted_keys:
                report.skipped.append(key)
        return report

    logger.info(
        f"Incremental sync: {len(new_keys)} new, {len(modified_keys)} modified, "
        f"{len(deleted_keys)} deleted"
    )

    pdf_paths = zot.get_pdf_paths_for_keys(list(keys_to_process))

    for key in keys_to_process:
        pdf_path = pdf_paths.get(key)
        if not pdf_path:
            report.skipped.append(key)
            state.item_versions[key] = current_versions[key]
            continue

        try:
            pages = extract_pdf_text(pdf_path)
            if not pages:
                report.failed.append({"key": key, "error": "no text extracted"})
                continue

            chunks = chunk_text(pages, chunk_size=chunk_size, overlap=chunk_overlap)
            item = zot.get_item(key)
            year = ZoteroClient.parse_year(item.date)
            indexer.index_chunks(chunks, item_key=key, title=item.title, year=year)

            if key in new_keys:
                report.added.append(key)
            else:
                report.updated.append(key)
            state.item_versions[key] = current_versions[key]
        except Exception as e:
            logger.error(f"sync_index failed for {key}: {e}")
            report.failed.append({"key": key, "error": str(e)})

    for key in current_versions:
        if key not in keys_to_process and key not in deleted_keys:
            if key not in state.item_versions:
                state.item_versions[key] = current_versions[key]

    state.embedding_model = embedding_model
    state.save()
    report.total_chunks_after = indexer.count()
    return report
