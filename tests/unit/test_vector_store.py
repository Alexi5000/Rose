"""Unit tests for Vector Store operations.

Tests storing memories in Qdrant, searching with similarity scores,
and duplicate detection with mocked Qdrant client.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from ai_companion.core.privacy_logging import REDACTED_TEXT, session_id_for_log
from ai_companion.modules.memory.long_term.vector_store import (
    DEFAULT_SESSION_ID,
    Memory,
    VectorStore,
    get_vector_store,
)


@pytest.fixture
def mock_vector_store_deps():
    """Mock all VectorStore dependencies."""
    with patch("ai_companion.modules.memory.long_term.vector_store.QdrantClient") as mock_client_class:
        with patch("ai_companion.modules.memory.long_term.vector_store.SentenceTransformer") as mock_model_class:
            with patch("ai_companion.modules.memory.long_term.vector_store.get_qdrant_circuit_breaker") as mock_cb:
                # Reset singleton state
                VectorStore._instance = None
                VectorStore._initialized = False

                mock_client = MagicMock()
                mock_model = MagicMock()
                mock_circuit_breaker = MagicMock()

                mock_client_class.return_value = mock_client
                mock_model_class.return_value = mock_model
                mock_cb.return_value = mock_circuit_breaker

                # Mock encode to return numpy array
                mock_model.encode.return_value = np.array([0.1] * 384)

                # Mock circuit breaker to pass through calls and execute the function
                def circuit_breaker_call(func, *args, **kwargs):
                    return func(*args, **kwargs)

                mock_circuit_breaker.call.side_effect = circuit_breaker_call

                yield {"client": mock_client, "model": mock_model, "circuit_breaker": mock_circuit_breaker}


@pytest.mark.unit
class TestMemoryStorage:
    """Test storing memories in Qdrant."""

    def test_store_new_memory(self, mock_vector_store_deps):
        """Test storing a new memory in the vector store."""
        mock_client = mock_vector_store_deps["client"]

        # Mock collection exists
        mock_client.get_collections.return_value.collections = [MagicMock(name="long_term_memory")]

        store = VectorStore()

        memory_text = "User is experiencing anxiety about work deadlines"
        metadata = {"id": "test_id_123", "timestamp": datetime.now().isoformat()}

        store.store_memory(memory_text, metadata)

        # Verify upsert was called
        mock_client.upsert.assert_called_once()
        call_args = mock_client.upsert.call_args
        assert call_args[1]["collection_name"] == "long_term_memory"
        assert len(call_args[1]["points"]) == 1

    def test_store_memory_creates_collection_if_not_exists(self, mock_vector_store_deps):
        """Test that collection is created if it doesn't exist."""
        mock_client = mock_vector_store_deps["client"]

        # Mock collection doesn't exist
        mock_client.get_collections.return_value.collections = []

        store = VectorStore()
        store.store_memory("Test memory", {"id": "test_id"})

        # Verify collection was created
        mock_client.create_collection.assert_called_once()

    def test_store_memory_with_metadata(self, mock_vector_store_deps):
        """Test that memory is stored with proper metadata."""
        mock_client = mock_vector_store_deps["client"]

        mock_client.get_collections.return_value.collections = [MagicMock(name="long_term_memory")]

        store = VectorStore()

        memory_text = "User finds deep breathing exercises helpful"
        metadata = {
            "id": "mem_456",
            "timestamp": "2024-01-15T10:30:00Z",
            "emotion": "calm",
            "topic": "coping_strategies",
        }

        store.store_memory(memory_text, metadata)

        # Verify metadata was included in the point
        call_args = mock_client.upsert.call_args
        point = call_args[1]["points"][0]
        assert point.payload["text"] == memory_text
        assert point.payload["id"] == "mem_456"
        assert point.payload["emotion"] == "calm"
        assert point.payload["session_id"] == DEFAULT_SESSION_ID

    def test_store_memory_generates_embedding(self, mock_vector_store_deps):
        """Test that memory text is converted to embedding."""
        mock_client = mock_vector_store_deps["client"]
        mock_model = mock_vector_store_deps["model"]

        mock_client.get_collections.return_value.collections = [MagicMock(name="long_term_memory")]

        store = VectorStore()
        memory_text = "Test memory for embedding"

        store.store_memory(memory_text, {"id": "test"})

        # Verify encode was called with the memory text
        mock_model.encode.assert_called()

    def test_store_memory_tags_payload_with_session_id_when_provided(self, mock_vector_store_deps):
        """Test that stored memories keep session metadata for export/delete controls."""
        mock_client = mock_vector_store_deps["client"]

        mock_collection = MagicMock()
        mock_collection.name = "long_term_memory"
        mock_client.get_collections.return_value.collections = [mock_collection]

        store = VectorStore()
        store.store_memory("User likes quiet morning rituals", {"id": "mem-session"}, session_id="session-123")

        point = mock_client.upsert.call_args[1]["points"][0]
        assert point.payload["session_id"] == "session-123"

    def test_store_memory_failure_log_redacts_provider_error(self, mock_vector_store_deps, monkeypatch, caplog):
        """Qdrant errors may echo payloads; storage logs should redact by default."""

        mock_client = mock_vector_store_deps["client"]
        monkeypatch.setattr("ai_companion.settings.settings.LOG_SENSITIVE_CONTENT", False)

        mock_collection = MagicMock()
        mock_collection.name = "long_term_memory"
        mock_client.get_collections.return_value.collections = [mock_collection]
        mock_client.search.return_value = []
        mock_client.upsert.side_effect = RuntimeError("qdrant echoed private grief memory payload")

        store = VectorStore()

        with caplog.at_level("WARNING", logger="ai_companion.modules.memory.long_term.vector_store"):
            store.store_memory("User has a private grief memory", {"id": "mem-private"}, session_id="session-private")

        assert "private grief" not in caplog.text
        assert REDACTED_TEXT in caplog.text
        assert "memory_store_failed" in caplog.text

    def test_store_memory_defaults_to_isolated_session_when_missing(self, mock_vector_store_deps):
        """Test the safe default does not store unscoped memories."""
        mock_client = mock_vector_store_deps["client"]

        mock_collection = MagicMock()
        mock_collection.name = "long_term_memory"
        mock_client.get_collections.return_value.collections = [mock_collection]

        store = VectorStore()
        store.store_memory("User wants privacy by default", {"id": "mem-default"})

        point = mock_client.upsert.call_args[1]["points"][0]
        assert point.payload["session_id"] == DEFAULT_SESSION_ID


@pytest.mark.unit
class TestMemorySearch:
    """Test searching memories with similarity scores."""

    def test_search_memories_returns_results(self, mock_vector_store_deps):
        """Test searching for similar memories returns results."""
        mock_client = mock_vector_store_deps["client"]

        # Mock collection exists - need to return a mock with collections attribute
        mock_collections_response = MagicMock()
        mock_collection = MagicMock()
        mock_collection.name = "long_term_memory"
        mock_collections_response.collections = [mock_collection]
        mock_client.get_collections.return_value = mock_collections_response

        # Mock search results
        mock_hit1 = MagicMock()
        mock_hit1.score = 0.95
        mock_hit1.payload = {
            "text": "User mentioned feeling anxious about work deadlines",
            "id": "mem1",
            "timestamp": "2024-01-15T10:30:00Z",
        }

        mock_hit2 = MagicMock()
        mock_hit2.score = 0.87
        mock_hit2.payload = {
            "text": "User finds deep breathing exercises helpful for anxiety",
            "id": "mem2",
            "timestamp": "2024-01-14T15:20:00Z",
        }

        mock_client.search.return_value = [mock_hit1, mock_hit2]

        store = VectorStore()
        results = store.search_memories("I'm feeling anxious", k=2)

        # Verify results
        assert len(results) == 2
        assert results[0].text == "User mentioned feeling anxious about work deadlines"
        assert results[0].score == 0.95
        assert results[1].text == "User finds deep breathing exercises helpful for anxiety"
        assert results[1].score == 0.87

    def test_search_memories_handles_qdrant_errors(self, mock_vector_store_deps):
        """Test that search returns empty list when Qdrant raises an unexpected error."""
        mock_client = mock_vector_store_deps["client"]

        # Mock collection exists
        mock_collections_response = MagicMock()
        mock_collection = MagicMock()
        mock_collection.name = "long_term_memory"
        mock_collections_response.collections = [mock_collection]
        mock_client.get_collections.return_value = mock_collections_response

        # Mock client.search to raise an internal exception
        def _raise():
            raise Exception("OutputTooSmall: qdrant internal panic")

        mock_client.search.side_effect = _raise

        store = VectorStore()
        results = store.search_memories("simulate error")

        # Should return empty list and not raise
        assert results == []

    def test_search_memories_error_log_redacts_query_echo(self, mock_vector_store_deps, monkeypatch, caplog):
        """Search failures should not log provider-echoed query text."""

        mock_client = mock_vector_store_deps["client"]
        monkeypatch.setattr("ai_companion.settings.settings.LOG_SENSITIVE_CONTENT", False)

        mock_collection = MagicMock()
        mock_collection.name = "long_term_memory"
        mock_client.get_collections.return_value.collections = [mock_collection]
        mock_client.search.side_effect = RuntimeError("qdrant echoed private grief query")

        store = VectorStore()

        with caplog.at_level("WARNING", logger="ai_companion.modules.memory.long_term.vector_store"):
            results = store.search_memories("private grief query", session_id="session-private")

        assert results == []
        assert "private grief" not in caplog.text
        assert REDACTED_TEXT in caplog.text
        assert "memory_search_failed" in caplog.text

    def test_search_memories_with_k_parameter(self, mock_vector_store_deps):
        """Test that search respects the k parameter."""
        mock_client = mock_vector_store_deps["client"]

        # Mock collection exists
        mock_collections_response = MagicMock()
        mock_collection = MagicMock()
        mock_collection.name = "long_term_memory"
        mock_collections_response.collections = [mock_collection]
        mock_client.get_collections.return_value = mock_collections_response

        mock_client.search.return_value = []

        store = VectorStore()
        store.search_memories("test query", k=5)

        # Verify search was called with correct limit
        call_args = mock_client.search.call_args
        assert call_args[1]["limit"] == 5

    def test_search_memories_filters_to_session_when_provided(self, mock_vector_store_deps):
        """Test semantic retrieval cannot cross session boundaries by default."""
        mock_client = mock_vector_store_deps["client"]

        mock_collection = MagicMock()
        mock_collection.name = "long_term_memory"
        mock_client.get_collections.return_value.collections = [mock_collection]
        mock_client.search.return_value = []

        store = VectorStore()
        store.search_memories("privacy", session_id="session-123")

        query_filter = mock_client.search.call_args[1]["query_filter"]
        assert query_filter.must[0].key == "session_id"
        assert query_filter.must[0].match.value == "session-123"

    def test_search_memories_uses_default_session_filter_when_missing(self, mock_vector_store_deps):
        """Test missing session IDs do not fall back to global memory search."""
        mock_client = mock_vector_store_deps["client"]

        mock_collection = MagicMock()
        mock_collection.name = "long_term_memory"
        mock_client.get_collections.return_value.collections = [mock_collection]
        mock_client.search.return_value = []

        store = VectorStore()
        store.search_memories("privacy")

        query_filter = mock_client.search.call_args[1]["query_filter"]
        assert query_filter.must[0].key == "session_id"
        assert query_filter.must[0].match.value == DEFAULT_SESSION_ID

    def test_search_memories_returns_empty_if_no_collection(self, mock_vector_store_deps):
        """Test that search returns empty list if collection doesn't exist."""
        mock_client = mock_vector_store_deps["client"]

        # Mock collection doesn't exist
        mock_client.get_collections.return_value.collections = []

        store = VectorStore()
        results = store.search_memories("test query")

        # Verify empty list returned
        assert results == []
        # Verify search was not called
        mock_client.search.assert_not_called()

    def test_search_memories_includes_metadata(self, mock_vector_store_deps):
        """Test that search results include metadata."""
        mock_client = mock_vector_store_deps["client"]

        # Mock collection exists
        mock_collections_response = MagicMock()
        mock_collection = MagicMock()
        mock_collection.name = "long_term_memory"
        mock_collections_response.collections = [mock_collection]
        mock_client.get_collections.return_value = mock_collections_response

        mock_hit = MagicMock()
        mock_hit.score = 0.92
        mock_hit.payload = {
            "text": "User has been working on mindfulness practices",
            "id": "mem3",
            "timestamp": "2024-01-13T09:15:00Z",
            "topic": "mindfulness",
        }

        mock_client.search.return_value = [mock_hit]

        store = VectorStore()
        results = store.search_memories("mindfulness")

        # Verify metadata is included
        assert results[0].metadata["id"] == "mem3"
        assert results[0].metadata["topic"] == "mindfulness"
        assert "text" not in results[0].metadata  # text should be separate


@pytest.mark.unit
class TestMemoryPrivacyOperations:
    """Test session export and deletion operations."""

    def test_export_memories_for_session_scrolls_without_vectors(self, mock_vector_store_deps):
        mock_client = mock_vector_store_deps["client"]

        mock_collection = MagicMock()
        mock_collection.name = "long_term_memory"
        mock_client.get_collections.return_value.collections = [mock_collection]

        mock_record = MagicMock()
        mock_record.payload = {
            "text": "User prefers gentler breathwork.",
            "id": "mem-1",
            "session_id": "session-123",
        }
        mock_client.scroll.return_value = ([mock_record], None)

        store = VectorStore()
        memories = store.export_memories_for_session("session-123")

        assert len(memories) == 1
        assert memories[0].text == "User prefers gentler breathwork."
        assert memories[0].metadata == {"id": "mem-1", "session_id": "session-123"}

        call_args = mock_client.scroll.call_args[1]
        assert call_args["collection_name"] == "long_term_memory"
        assert call_args["with_vectors"] is False
        assert call_args["scroll_filter"].must[0].key == "session_id"
        assert call_args["scroll_filter"].must[0].match.value == "session-123"

    def test_delete_memories_for_session_uses_filter_selector(self, mock_vector_store_deps):
        mock_client = mock_vector_store_deps["client"]

        mock_collection = MagicMock()
        mock_collection.name = "long_term_memory"
        mock_client.get_collections.return_value.collections = [mock_collection]

        store = VectorStore()
        deleted = store.delete_memories_for_session("session-123")

        assert deleted is True
        call_args = mock_client.delete.call_args[1]
        assert call_args["collection_name"] == "long_term_memory"
        assert call_args["wait"] is True
        assert call_args["points_selector"].filter.must[0].key == "session_id"
        assert call_args["points_selector"].filter.must[0].match.value == "session-123"

    def test_export_failure_log_redacts_exception_and_hashes_session(self, mock_vector_store_deps, monkeypatch, caplog):
        mock_client = mock_vector_store_deps["client"]
        monkeypatch.setattr("ai_companion.settings.settings.LOG_SENSITIVE_CONTENT", False)

        mock_collection = MagicMock()
        mock_collection.name = "long_term_memory"
        mock_client.get_collections.return_value.collections = [mock_collection]
        mock_client.scroll.side_effect = RuntimeError("export echoed private grief memory")

        store = VectorStore()

        with caplog.at_level("WARNING", logger="ai_companion.modules.memory.long_term.vector_store"):
            memories = store.export_memories_for_session("session-private")

        assert memories == []
        assert "private grief" not in caplog.text
        assert "session-private" not in caplog.text
        assert REDACTED_TEXT in caplog.text
        assert session_id_for_log("session-private") in caplog.text

    def test_delete_failure_log_redacts_exception_and_hashes_session(self, mock_vector_store_deps, monkeypatch, caplog):
        mock_client = mock_vector_store_deps["client"]
        monkeypatch.setattr("ai_companion.settings.settings.LOG_SENSITIVE_CONTENT", False)

        mock_collection = MagicMock()
        mock_collection.name = "long_term_memory"
        mock_client.get_collections.return_value.collections = [mock_collection]
        mock_client.delete.side_effect = RuntimeError("delete echoed private grief memory")

        store = VectorStore()

        with caplog.at_level("WARNING", logger="ai_companion.modules.memory.long_term.vector_store"):
            deleted = store.delete_memories_for_session("session-private")

        assert deleted is False
        assert "private grief" not in caplog.text
        assert "session-private" not in caplog.text
        assert REDACTED_TEXT in caplog.text
        assert session_id_for_log("session-private") in caplog.text


@pytest.mark.unit
class TestDuplicateDetection:
    """Test finding similar memories (duplicate detection)."""

    def test_find_similar_memory_returns_match(self, mock_vector_store_deps):
        """Test finding a similar memory above threshold."""
        mock_client = mock_vector_store_deps["client"]

        # Mock collection exists
        mock_collections_response = MagicMock()
        mock_collection = MagicMock()
        mock_collection.name = "long_term_memory"
        mock_collections_response.collections = [mock_collection]
        mock_client.get_collections.return_value = mock_collections_response

        # Mock a high similarity match
        mock_hit = MagicMock()
        mock_hit.score = 0.95  # Above threshold (0.9)
        mock_hit.payload = {
            "text": "Name is Sarah, lives in Portland",
            "id": "existing_mem",
            "timestamp": "2024-01-01T00:00:00Z",
        }

        mock_client.search.return_value = [mock_hit]

        store = VectorStore()
        similar = store.find_similar_memory("Name is Sarah, lives in Portland")

        # Verify similar memory was found
        assert similar is not None
        assert similar.text == "Name is Sarah, lives in Portland"
        assert similar.score == 0.95

    def test_find_similar_memory_returns_none_below_threshold(self, mock_vector_store_deps):
        """Test that memories below similarity threshold are not considered duplicates."""
        mock_client = mock_vector_store_deps["client"]

        mock_client.get_collections.return_value.collections = [MagicMock(name="long_term_memory")]

        # Mock a low similarity match
        mock_hit = MagicMock()
        mock_hit.score = 0.75  # Below threshold (0.9)
        mock_hit.payload = {"text": "Different memory content", "id": "other_mem"}

        mock_client.search.return_value = [mock_hit]

        store = VectorStore()
        similar = store.find_similar_memory("Name is Sarah, lives in Portland")

        # Verify no similar memory found
        assert similar is None

    def test_find_similar_memory_returns_none_if_no_results(self, mock_vector_store_deps):
        """Test that None is returned when no memories exist."""
        mock_client = mock_vector_store_deps["client"]

        mock_client.get_collections.return_value.collections = [MagicMock(name="long_term_memory")]
        mock_client.search.return_value = []

        store = VectorStore()
        similar = store.find_similar_memory("New unique memory")

        # Verify None returned
        assert similar is None

    def test_find_similar_memory_uses_top_1(self, mock_vector_store_deps):
        """Test that duplicate detection only checks the top result."""
        mock_client = mock_vector_store_deps["client"]

        # Mock collection exists
        mock_collections_response = MagicMock()
        mock_collection = MagicMock()
        mock_collection.name = "long_term_memory"
        mock_collections_response.collections = [mock_collection]
        mock_client.get_collections.return_value = mock_collections_response

        mock_client.search.return_value = []

        store = VectorStore()
        store.find_similar_memory("test")

        # Verify search was called with k=1
        call_args = mock_client.search.call_args
        assert call_args[1]["limit"] == 1


@pytest.mark.unit
class TestMemoryDataClass:
    """Test Memory data class properties."""

    def test_memory_properties(self):
        """Test Memory data class properties."""
        memory = Memory(
            text="User is experiencing grief",
            metadata={"id": "mem_123", "timestamp": "2024-01-15T10:00:00Z", "emotion": "sadness"},
            score=0.92,
        )

        assert memory.text == "User is experiencing grief"
        assert memory.id == "mem_123"
        assert memory.score == 0.92
        assert memory.metadata["emotion"] == "sadness"

    def test_memory_timestamp_property(self):
        """Test Memory timestamp property parsing."""
        memory = Memory(text="Test memory", metadata={"timestamp": "2024-01-15T10:30:00"}, score=0.85)

        timestamp = memory.timestamp
        assert timestamp is not None
        assert timestamp.year == 2024
        assert timestamp.month == 1
        assert timestamp.day == 15

    def test_memory_without_id(self):
        """Test Memory without id in metadata."""
        memory = Memory(text="Test memory", metadata={}, score=0.80)

        assert memory.id is None

    def test_memory_without_timestamp(self):
        """Test Memory without timestamp in metadata."""
        memory = Memory(text="Test memory", metadata={"id": "test"}, score=0.80)

        assert memory.timestamp is None


@pytest.mark.unit
class TestVectorStoreSingleton:
    """Test VectorStore singleton pattern."""

    def test_get_vector_store_returns_singleton(self, mock_vector_store_deps):
        """Test that get_vector_store returns the same instance."""
        # Clear the lru_cache
        get_vector_store.cache_clear()

        store1 = get_vector_store()
        store2 = get_vector_store()

        # Verify same instance
        assert store1 is store2
