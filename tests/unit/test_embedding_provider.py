"""Unit tests for embedding provider selection."""

from unittest.mock import MagicMock, patch

import pytest

from ai_companion.modules.memory.embedding_provider import (
    EmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
    get_embedding_provider,
)
from ai_companion.settings import settings


def test_get_embedding_provider_defaults_to_sentence_transformer(monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "sentence_transformer")
    mock_model = MagicMock()

    provider = get_embedding_provider(model=mock_model)

    assert isinstance(provider, SentenceTransformerEmbeddingProvider)
    assert isinstance(provider, EmbeddingProvider)
    assert provider.name == "sentence_transformer"
    assert provider.model is mock_model


def test_get_embedding_provider_accepts_local_alias(monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "local")

    with patch("ai_companion.modules.memory.embedding_provider.SentenceTransformer") as mock_model:
        provider = get_embedding_provider()

    assert isinstance(provider, SentenceTransformerEmbeddingProvider)
    mock_model.assert_called_once()


def test_get_embedding_provider_rejects_unknown_provider(monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "unknown")

    with pytest.raises(ValueError, match="Unsupported EMBEDDING_PROVIDER"):
        get_embedding_provider(model=MagicMock())


def test_sentence_transformer_provider_embeds_text():
    mock_model = MagicMock()
    mock_model.encode.return_value = [0.1, 0.2]
    provider = SentenceTransformerEmbeddingProvider(model=mock_model)

    assert provider.embed_text("quiet ritual") == [0.1, 0.2]
    mock_model.encode.assert_called_once_with("quiet ritual")
