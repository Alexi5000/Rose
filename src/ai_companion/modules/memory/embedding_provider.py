"""Embedding provider abstraction for Rose memory retrieval."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from sentence_transformers import SentenceTransformer

from ai_companion.settings import settings


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol for text embedding providers."""

    name: str
    model_name: str

    def embed_text(self, text: str) -> Any:
        """Return an embedding vector for one text input."""
        ...


def _default_embedding_model_name() -> str:
    from ai_companion.modules.memory.long_term.constants import EMBEDDING_MODEL_NAME

    return EMBEDDING_MODEL_NAME


class SentenceTransformerEmbeddingProvider:
    """Local sentence-transformer embedding provider."""

    name = "sentence_transformer"

    def __init__(self, model: Any | None = None, model_name: str | None = None) -> None:
        self.model_name = model_name or _default_embedding_model_name()
        self.model = model or SentenceTransformer(self.model_name)

    def embed_text(self, text: str) -> Any:
        """Return an embedding vector for one text input."""
        return self.model.encode(text)


def get_embedding_provider(model: Any | None = None) -> EmbeddingProvider:
    """Create the configured embedding provider."""
    provider = settings.EMBEDDING_PROVIDER.strip().lower()
    if provider in {"sentence_transformer", "sentence-transformer", "local"}:
        return SentenceTransformerEmbeddingProvider(model=model)
    raise ValueError(f"Unsupported EMBEDDING_PROVIDER '{settings.EMBEDDING_PROVIDER}'")
