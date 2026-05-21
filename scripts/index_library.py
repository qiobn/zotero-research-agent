"""One-shot indexing/sync script. Equivalent to calling the sync_index tool."""

from __future__ import annotations

import time

from loguru import logger
from research_core.rag.indexer import Indexer
from research_core.rag.retriever import Retriever
from research_core.tools.admin import sync_index
from research_core.zotero.client import ZoteroClient


def main(force_rebuild: bool = False):
    zot = ZoteroClient(library_id="0", local=True)
    indexer = Indexer(persist_dir=".chroma_db")
    retriever = Retriever(persist_dir=".chroma_db")

    t0 = time.time()
    report = sync_index(zot, indexer, retriever, force_rebuild=force_rebuild)
    elapsed = time.time() - t0

    logger.info(f"Sync done in {elapsed:.1f}s (incremental={report.incremental})")
    logger.info(f"  added:   {len(report.added)}")
    logger.info(f"  updated: {len(report.updated)}")
    logger.info(f"  skipped: {len(report.skipped)}")
    logger.info(f"  removed: {len(report.removed)}")
    logger.info(f"  failed:  {len(report.failed)}")
    logger.info(f"  total chunks now: {report.total_chunks_after}")
    if report.failed:
        for f in report.failed:
            logger.warning(f"  failed: {f}")


if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    main(force_rebuild=force)
