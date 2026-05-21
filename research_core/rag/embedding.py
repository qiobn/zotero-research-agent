"""Shared embedding function for ChromaDB backed by sentence-transformers.

Loads the model once (lazy singleton). Defaults to BAAI/bge-m3 which supports
Chinese + English + multilingual with 1024-dim dense vectors.
"""

from __future__ import annotations

import os

from chromadb.api.types import (
    Documents,
    EmbeddingFunction,
    Embeddings,
)
from loguru import logger

_DEFAULT_MODEL = "BAAI/bge-m3"


class SentenceTransformerEmbedding(EmbeddingFunction[Documents]):
    """ChromaDB-compatible wrapper around sentence-transformers."""

    def __init__(self, model_name: str | None = None):
        self._model_name = model_name or os.getenv("EMBEDDING_MODEL", _DEFAULT_MODEL)
        self._model = None

    def name(self) -> str:
        return f"sentence-transformer-{self._model_name}"

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {self._model_name}")
            self._model = SentenceTransformer(self._model_name)
            logger.info(f"Embedding model loaded, dim={self._model.get_embedding_dimension()}")

    def __call__(self, input: Documents) -> Embeddings:
        self._load()
        embeddings = self._model.encode(input, normalize_embeddings=True)
        return embeddings.tolist()


_singleton: SentenceTransformerEmbedding | None = None


def get_embedding_function() -> SentenceTransformerEmbedding:
    """Return a singleton embedding function. Thread-safe for single-process use."""
    global _singleton
    if _singleton is None:
        _singleton = SentenceTransformerEmbedding()
    return _singleton
