"""Local embedding generation using fastembed (free, no API key).

Uses BAAI/bge-small-en-v1.5 by default — runs on CPU via ONNX runtime.
384-dimensional vectors, suitable for pgvector similarity search.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.config import settings
from src.core.exceptions import EmbeddingError
from src.logging_config import get_logger

if TYPE_CHECKING:
    from fastembed import TextEmbedding

log = get_logger(__name__)

_model: TextEmbedding | None = None


def _get_model() -> TextEmbedding:
    global _model
    if _model is None:
        from fastembed import TextEmbedding

        log.info("loading_embedding_model", model=settings.embedding_model)
        _model = TextEmbedding(model_name=settings.embedding_model)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of texts."""
    if not texts:
        return []
    try:
        model = _get_model()
        embeddings = list(model.embed(texts))
        return [e.tolist() for e in embeddings]
    except Exception as e:
        log.error("embedding_failed", error=str(e))
        raise EmbeddingError(f"Embedding generation failed: {e}") from e


def embed_text(text: str) -> list[float]:
    """Generate embedding for a single text."""
    results = embed_texts([text])
    if not results:
        raise EmbeddingError("No embedding returned")
    return results[0]
