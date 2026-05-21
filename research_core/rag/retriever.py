"""Retrieve relevant chunks from ChromaDB."""

from __future__ import annotations

from dataclasses import dataclass, field

import chromadb

from research_core.rag.embedding import get_embedding_function


@dataclass
class RetrievalResult:
    text: str
    item_key: str
    title: str
    page_start: int
    page_end: int
    score: float
    chunk_idx: int = 0
    metadata: dict = field(default_factory=dict)


class Retriever:
    """Query the ChromaDB collection for semantically similar chunks."""

    def __init__(
        self,
        persist_dir: str = ".chroma_db",
        collection_name: str = "research_chunks",
    ):
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=get_embedding_function(),
        )

    def search(
        self,
        query: str,
        n_results: int = 8,
        where: dict | None = None,
    ) -> list[RetrievalResult]:
        """Semantic search across all indexed chunks (optionally filtered by metadata)."""
        kwargs = {"query_texts": [query], "n_results": n_results}
        if where:
            kwargs["where"] = where
        results = self._collection.query(**kwargs)
        return self._to_results(results)

    def search_within_item(
        self,
        item_key: str,
        query: str,
        n_results: int = 5,
    ) -> list[RetrievalResult]:
        """Semantic search restricted to a single paper's chunks."""
        return self.search(query, n_results=n_results, where={"item_key": item_key})

    def get_item_chunks(
        self,
        item_key: str,
        page: int | None = None,
    ) -> list[RetrievalResult]:
        """Retrieve all chunks of one paper, optionally filtered by page number."""
        where: dict = {"item_key": item_key}
        if page is not None:
            where = {
                "$and": [
                    {"item_key": item_key},
                    {"page_start": {"$lte": page}},
                    {"page_end": {"$gte": page}},
                ]
            }
        raw = self._collection.get(where=where, include=["documents", "metadatas"])
        docs = raw.get("documents", []) or []
        metas = raw.get("metadatas", []) or []
        out: list[RetrievalResult] = []
        for doc, meta in zip(docs, metas, strict=True):
            out.append(
                RetrievalResult(
                    text=doc,
                    item_key=meta.get("item_key", ""),
                    title=meta.get("title", ""),
                    page_start=meta.get("page_start", 0),
                    page_end=meta.get("page_end", 0),
                    score=1.0,
                    chunk_idx=meta.get("chunk_idx", 0),
                    metadata=meta,
                )
            )
        out.sort(key=lambda r: r.chunk_idx)
        return out

    def list_indexed_items(self) -> set[str]:
        """Return the set of item_keys currently indexed in the vector store."""
        raw = self._collection.get(include=["metadatas"])
        metas = raw.get("metadatas", []) or []
        return {m.get("item_key", "") for m in metas if m.get("item_key")}

    def count(self) -> int:
        return self._collection.count()

    @staticmethod
    def _to_results(raw: dict) -> list[RetrievalResult]:
        if not raw or not raw.get("documents"):
            return []
        docs = raw["documents"][0]
        metas = raw["metadatas"][0] if raw.get("metadatas") else [{}] * len(docs)
        dists = raw["distances"][0] if raw.get("distances") else [0.0] * len(docs)
        out: list[RetrievalResult] = []
        for doc, meta, dist in zip(docs, metas, dists, strict=True):
            out.append(
                RetrievalResult(
                    text=doc,
                    item_key=meta.get("item_key", ""),
                    title=meta.get("title", ""),
                    page_start=meta.get("page_start", 0),
                    page_end=meta.get("page_end", 0),
                    score=1 - dist,
                    chunk_idx=meta.get("chunk_idx", 0),
                    metadata=meta,
                )
            )
        return out
