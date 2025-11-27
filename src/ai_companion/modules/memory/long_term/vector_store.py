"""Vector storage operations for long-term memory using Qdrant.

This module provides the VectorStore class which handles all interactions with
the Qdrant vector database. It manages memory storage, retrieval, and similarity
search using sentence embeddings.

The vector store uses the 'all-MiniLM-L6-v2' model for generating embeddings,
which provides a good balance between performance and accuracy for semantic search.
Circuit breaker protection is applied to all Qdrant operations to handle service
unavailability gracefully.

Module Dependencies:
- ai_companion.core.resilience: Circuit breaker for Qdrant operations
- ai_companion.settings: Configuration for Qdrant URL, API key, collection settings
- qdrant_client: QdrantClient for vector database operations
- sentence_transformers: SentenceTransformer for embedding generation
- Standard library: os, dataclasses, datetime, functools, typing

Dependents (modules that import this):
- ai_companion.modules.memory.long_term.memory_manager: Memory persistence operations
- Test modules: tests/unit/test_vector_store.py

Architecture:
This module is part of the modules layer and implements the singleton pattern to
ensure only one Qdrant client instance exists, providing connection pooling and
efficient resource management. All Qdrant operations are protected by circuit
breakers to handle service unavailability gracefully.

For detailed architecture documentation, see:
- docs/ARCHITECTURE.md: Module Initialization Patterns section (Singleton Pattern)
- docs/ARCHITECTURE.md: Memory System Architecture section

Design Reference:
- .kiro/specs/technical-debt-management/design.md: Type Safety Enhancement section

Example:
    Basic usage of the vector store:

    >>> store = get_vector_store()
    >>> store.store_memory(
    ...     text="User prefers morning appointments",
    ...     metadata={"id": "mem_123", "timestamp": "2025-01-15T10:00:00"}
    ... )
    >>> results = store.search_memories("appointment preferences", k=5)
    >>> for memory in results:
    ...     print(f"{memory.text} (score: {memory.score})")
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import exceptions as qdrant_exceptions
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

from ai_companion.core.resilience import CircuitBreaker, CircuitBreakerError, get_qdrant_circuit_breaker
from ai_companion.core.metrics import metrics
from ai_companion.modules.memory.long_term.guard import guard as memory_guard
from ai_companion.core.retry import retry_with_exponential_backoff
from ai_companion.modules.memory.long_term.constants import (
    DEFAULT_MEMORY_SEARCH_LIMIT,
    DEFAULT_SESSION_ID,
    DUPLICATE_DETECTION_SIMILARITY_THRESHOLD,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_VECTOR_DIMENSIONS,
    ENABLE_SESSION_ISOLATION,
    LOG_CIRCUIT_BREAKER_EVENTS,
    LOG_DUPLICATE_DETECTION,
    LOG_MEMORY_SEARCH_SCORES,
    QDRANT_COLLECTION_NAME,
    SESSION_ID_METADATA_KEY,
)
from ai_companion.settings import settings

# Type aliases for common memory types
type MemoryMetadata = dict[str, Any]
type MemorySearchResult = list[Memory]
type CollectionInfo = dict[str, Any]


@dataclass
class Memory:
    """Represents a memory entry in the vector store."""

    text: str
    metadata: MemoryMetadata
    score: Optional[float] = None

    @property
    def id(self) -> Optional[str]:
        return self.metadata.get("id")

    @property
    def timestamp(self) -> Optional[datetime]:
        ts: Optional[str] = self.metadata.get("timestamp")
        return datetime.fromisoformat(ts) if ts else None


class VectorStore:
    """A class to handle vector storage operations using Qdrant.

    Implements singleton pattern to ensure only one Qdrant client instance
    is created and reused across all requests, providing connection pooling
    and efficient resource management.

    Features:
    - 🔒 Session-based isolation for multi-user deployments
    - ♻️ Automatic duplicate detection using semantic similarity
    - ⚡ Circuit breaker protection for resilience
    - 📊 Comprehensive logging of all operations
    - 🎯 Configurable via constants (no magic numbers)
    """

    _instance: Optional["VectorStore"] = None
    _initialized: bool = False

    def __new__(cls) -> "VectorStore":
        """Ensure only one instance of VectorStore exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize VectorStore with Qdrant client (only once due to singleton).

        The Qdrant client maintains an internal connection pool for efficient
        request handling across multiple concurrent operations.

        Configuration:
        - QDRANT_URL: Connection URL (required)
        - QDRANT_API_KEY: API key (optional for local deployments)
        - Embedding model: Configured via constants.EMBEDDING_MODEL_NAME
        """
        if not self._initialized:
            self.logger = logging.getLogger(__name__)
            self.model: SentenceTransformer = SentenceTransformer(EMBEDDING_MODEL_NAME)

            # 🔧 Initialize Qdrant client with optional API key support
            # API key is only required for Qdrant Cloud, not for local Docker deployments
            if settings.QDRANT_API_KEY and settings.QDRANT_API_KEY.lower() not in ["none", "", "null"]:
                self.logger.info("🔐 Initializing Qdrant client with API key authentication")
                self.client: QdrantClient = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
            else:
                self.logger.info(f"🌐 Initializing Qdrant client for local deployment: {settings.QDRANT_URL}")
                self.client: QdrantClient = QdrantClient(url=settings.QDRANT_URL)

            self._circuit_breaker: CircuitBreaker = get_qdrant_circuit_breaker()
            VectorStore._initialized = True
            self.logger.info(
                f"✅ VectorStore initialized (model: {EMBEDDING_MODEL_NAME}, collection: {QDRANT_COLLECTION_NAME})"
            )

    def _collection_exists(self) -> bool:
        """Check if the memory collection exists.

        Returns:
            bool: True if collection exists, False otherwise (including when circuit breaker is open)
        """
        try:
            collections = self._circuit_breaker.call(self.client.get_collections).collections
            exists = any(col.name == QDRANT_COLLECTION_NAME for col in collections)
            if exists:
                self.logger.debug(f"✅ Collection '{QDRANT_COLLECTION_NAME}' exists")
            else:
                self.logger.debug(f"📭 Collection '{QDRANT_COLLECTION_NAME}' does not exist")
            return exists
        except CircuitBreakerError:
            if LOG_CIRCUIT_BREAKER_EVENTS:
                self.logger.warning("⚡ Circuit breaker OPEN: Cannot check collection existence")
            return False

    def _create_collection(self) -> None:
        """Create a new collection for storing memories with proper vector configuration.

        Collection schema:
        - Vector dimensions: Determined by embedding model (384 for all-MiniLM-L6-v2)
        - Distance metric: COSINE (best for semantic similarity)
        - Payload schema: Flexible (no strict schema, allows any metadata)

        Raises:
            No exceptions raised; errors are logged via circuit breaker
        """
        sample_embedding = self.model.encode("sample text")
        vector_size = len(sample_embedding)

        self.logger.info(f"🏗️ Creating collection '{QDRANT_COLLECTION_NAME}' (dim={vector_size}, metric=COSINE)")

        def _create():
            return self.client.create_collection(
                collection_name=QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )

        try:
            self._circuit_breaker.call(_create)
            self.logger.info(f"✅ Collection '{QDRANT_COLLECTION_NAME}' created successfully")
        except CircuitBreakerError:
            if LOG_CIRCUIT_BREAKER_EVENTS:
                self.logger.error(f"⚡ Circuit breaker OPEN: Cannot create collection '{QDRANT_COLLECTION_NAME}'")

    def find_similar_memory(self, text: str, session_id: Optional[str] = None) -> Optional[Memory]:
        """Find if a similar memory already exists to prevent duplicates.

        Searches for memories with similarity score >= DUPLICATE_DETECTION_SIMILARITY_THRESHOLD.
        This high threshold ensures only near-duplicate memories are detected,
        allowing for variations in phrasing while preventing redundant storage.

        Args:
            text: The text to search for similar memories
            session_id: Optional session ID to filter by (if ENABLE_SESSION_ISOLATION is True)

        Returns:
            Optional[Memory]: The most similar memory if found above threshold, None otherwise

        Example:
            >>> similar = store.find_similar_memory("User likes coffee", session_id="user_123")
            >>> if similar:
            ...     print(f"Found similar: {similar.text} (score: {similar.score:.2f})")
            Found similar: User prefers coffee over tea (score: 0.94)
        """
        results = self.search_memories(text, k=1, session_id=session_id)
        if results and results[0].score and results[0].score >= DUPLICATE_DETECTION_SIMILARITY_THRESHOLD:
            if LOG_DUPLICATE_DETECTION:
                self.logger.info(
                    f"♻️ Duplicate detected: '{text[:60]}...' "
                    f"(similarity: {results[0].score:.2f} >= {DUPLICATE_DETECTION_SIMILARITY_THRESHOLD:.2f})"
                )
            return results[0]

        self.logger.debug(f"✅ No duplicate found for: '{text[:60]}...'")
        return None

    def store_memory(self, text: str, metadata: MemoryMetadata, session_id: Optional[str] = None) -> None:
        """Store a new memory in the vector store or update if similar exists.

        This method performs the following operations:
        1. Creates the collection if it doesn't exist
        2. Ensures session_id is present (uses DEFAULT_SESSION_ID if not provided)
        3. Checks for similar existing memories within the same session
        4. If similar memory found, updates it (keeps same ID)
        5. If new memory, generates embedding and stores with metadata

        Circuit breaker protection ensures graceful handling of Qdrant unavailability.

        Args:
            text: The text content of the memory to store
            metadata: Additional information (id, timestamp, etc.). Must include 'id' and 'timestamp'
            session_id: Session/user identifier for isolation (auto-added if ENABLE_SESSION_ISOLATION=True)

        Example:
            >>> store.store_memory(
            ...     text="User has a cat named Whiskers",
            ...     metadata={"id": "mem_456", "timestamp": "2025-01-15T14:30:00"},
            ...     session_id="user_123"
            ... )
        """
        try:
            if not self._collection_exists():
                self._create_collection()

            # 🔒 Ensure session isolation if enabled
            if ENABLE_SESSION_ISOLATION:
                effective_session_id = session_id or DEFAULT_SESSION_ID
                metadata[SESSION_ID_METADATA_KEY] = effective_session_id
                if not session_id:
                    self.logger.warning(
                        f"⚠️ No session_id provided, using default: {DEFAULT_SESSION_ID}. "
                        "This may cause data leakage in multi-user deployments!"
                    )
            else:
                effective_session_id = None

            # ♻️ Check if similar memory exists (prevents duplicates within session)
            similar_memory: Optional[Memory] = self.find_similar_memory(text, session_id=effective_session_id)
            if similar_memory and similar_memory.id:
                self.logger.info(f"🔄 Updating existing memory: {similar_memory.id}")
                metadata["id"] = similar_memory.id  # Keep same ID for update
            else:
                self.logger.info(f"💾 Storing new memory: '{text[:60]}...'")

            # 🧠 Generate embedding using sentence transformer model
            embedding: Any = self.model.encode(text)
            # Log embedding dimension for observability
            try:
                self.logger.debug(f"🧩 Memory embedding dimension: {len(embedding)}")
            except Exception:
                self.logger.debug("🧩 Memory embedding dimension: unknown")
            # Validate embedding shape/dimensions to avoid Qdrant panics
            if not hasattr(embedding, "__len__") or len(embedding) != EMBEDDING_VECTOR_DIMENSIONS:
                self.logger.warning(
                    "⚠️ Generated embedding has unexpected dimensions - skipping memory storage: "
                    f"dim={getattr(embedding, '__len__', lambda: 'unknown')()} expected={EMBEDDING_VECTOR_DIMENSIONS}"
                )
                return
            point: PointStruct = PointStruct(
                id=metadata.get("id", hash(text)),
                vector=embedding.tolist(),
                payload={
                    "text": text,
                    **metadata,
                },
            )

            def _upsert() -> Any:
                return self.client.upsert(
                    collection_name=QDRANT_COLLECTION_NAME,
                    points=[point],
                )

            # Wrap upsert with retry/backoff to mitigate transient Qdrant errors
            _upsert_with_retry = retry_with_exponential_backoff(
                max_retries=settings.QDRANT_MAX_RETRIES,
                initial_backoff=settings.QDRANT_INITIAL_BACKOFF,
                max_backoff=settings.QDRANT_MAX_BACKOFF,
            )(_upsert)

            try:
                self._circuit_breaker.call(_upsert_with_retry)
            except Exception as e:
                # Log and continue - memory storage shouldn't break the workflow
                self.logger.exception(f"⚠️ Failed to store memory to Qdrant: {type(e).__name__}: {str(e)}")
                return
            self.logger.debug(f"✅ Memory stored successfully: {metadata.get('id')}")

        except CircuitBreakerError:
            if LOG_CIRCUIT_BREAKER_EVENTS:
                self.logger.error(f"⚡ Circuit breaker OPEN: Cannot store memory. Text: {text[:50]}...")

    def search_memories(
        self, query: str, k: int = DEFAULT_MEMORY_SEARCH_LIMIT, session_id: Optional[str] = None
    ) -> MemorySearchResult:
        """Search for similar memories in the vector store using semantic search.

        Performs cosine similarity search on memory embeddings to find the most
        relevant memories for the given query. Results are ordered by similarity
        score (higher is more similar).

        If ENABLE_SESSION_ISOLATION is True, only memories from the specified
        session are returned (prevents cross-user data leakage).

        Args:
            query: Text to search for (will be embedded for similarity comparison)
            k: Number of results to return (default: DEFAULT_MEMORY_SEARCH_LIMIT = 5)
            session_id: Optional session ID to filter by (required if ENABLE_SESSION_ISOLATION=True)

        Returns:
            List[Memory]: Memory objects ordered by relevance (highest score first)
                         Empty list if collection doesn't exist or circuit breaker is open

        Example:
            >>> results = store.search_memories("dietary restrictions", k=3, session_id="user_123")
            >>> for memory in results:
            ...     print(f"{memory.text} (score: {memory.score:.2f})")
            User is allergic to peanuts (score: 0.92)
            User follows vegetarian diet (score: 0.85)
        """
        try:
            if not self._collection_exists():
                self.logger.debug("📭 Collection does not exist, cannot search")
                return []

            # 🔒 Ensure session isolation if enabled
            effective_session_id = None
            query_filter = None
            if ENABLE_SESSION_ISOLATION:
                effective_session_id = session_id or DEFAULT_SESSION_ID
                if not session_id:
                    self.logger.warning(f"⚠️ No session_id provided for search, using default: {DEFAULT_SESSION_ID}")
                # Create Qdrant filter for session-based retrieval
                query_filter = Filter(
                    must=[FieldCondition(key=SESSION_ID_METADATA_KEY, match=MatchValue(value=effective_session_id))]
                )

            self.logger.debug(f"🔍 Searching memories: query='{query[:60]}...', k={k}, session={effective_session_id}")

            # 🧠 Generate embedding for the query using the same model as storage
            query_embedding: Any = self.model.encode(query)
            # Log query embedding dimension for observability
            try:
                self.logger.debug(f"🧩 Query embedding dimension: {len(query_embedding)}")
            except Exception:
                self.logger.debug("🧩 Query embedding dimension: unknown")

            # Validate query embedding dimensions to avoid Qdrant internal panics
            if not hasattr(query_embedding, "__len__") or len(query_embedding) != EMBEDDING_VECTOR_DIMENSIONS:
                self.logger.warning(
                    "⚠️ Query embedding has unexpected dimensions - aborting search: "
                    f"dim={getattr(query_embedding, '__len__', lambda: 'unknown')()} expected={EMBEDDING_VECTOR_DIMENSIONS}"
                )
                return []

            def _search() -> List[Any]:
                return self.client.search(
                    collection_name=QDRANT_COLLECTION_NAME,
                    query_vector=query_embedding.tolist(),
                    limit=k,
                    query_filter=query_filter,  # Apply session filter if enabled
                )

            # If guard indicates Qdrant is degraded, skip search immediately and return empty list
            if memory_guard.is_disabled():
                self.logger.warning("⚠️ Qdrant is degraded; skipping memory search due to recent errors")
                return []

            # Wrap search with retry/backoff to handle transient Qdrant internal errors
            _search_with_retry = retry_with_exponential_backoff(
                max_retries=settings.QDRANT_MAX_RETRIES,
                initial_backoff=settings.QDRANT_INITIAL_BACKOFF,
                max_backoff=settings.QDRANT_MAX_BACKOFF,
            )(_search)

            results: List[Any] = self._circuit_breaker.call(_search_with_retry)

            # Convert Qdrant results to Memory objects
            memories = [
                Memory(
                    text=hit.payload["text"],
                    metadata={k: v for k, v in hit.payload.items() if k != "text"},
                    score=hit.score,
                )
                for hit in results
            ]

            # 📊 Log search results with scores
            if LOG_MEMORY_SEARCH_SCORES and memories:
                self.logger.info(f"🔍 Found {len(memories)} memories:")
                for memory in memories:
                    self.logger.info(f"  📌 '{memory.text[:60]}...' (score: {memory.score:.3f})")
            elif not memories:
                self.logger.debug(f"📭 No memories found for query: '{query[:60]}...'")

            return memories

        except CircuitBreakerError:
            if LOG_CIRCUIT_BREAKER_EVENTS:
                self.logger.error("⚡ Circuit breaker OPEN: Cannot search memories")
            return []
        except Exception as e:
            # Unexpected Qdrant or embedding errors should not crash the app
            # Log more details for qdrant UnexpectedResponse
            if isinstance(e, getattr(qdrant_exceptions, "UnexpectedResponse", (Exception,))):
                try:
                    status = getattr(e, "status", None)
                    content = getattr(e, "content", None)
                    self.logger.error(
                        "⚠️ UnexpectedResponse from Qdrant",
                        status=status,
                        content=str(content)[:500],
                        exc_info=True,
                    )
                except Exception:
                    self.logger.exception("⚠️ UnexpectedResponse from Qdrant (unable to extract details)")
                # Record metric for monitoring so alerting picks this up
                try:
                    metrics.record_error("qdrant_unexpected_response", endpoint="qdrant_search")
                    memory_guard.record_error()
                except Exception:
                    self.logger.debug("Failed to record qdrant_unexpected_response metric")
            else:
                self.logger.exception(
                    f"⚠️ Memory search failed with an unexpected error: {type(e).__name__}: {str(e)}"
                )
                try:
                    metrics.record_error("qdrant_unexpected_response", endpoint="qdrant_search")
                    memory_guard.record_error()
                except Exception:
                    self.logger.debug("Failed to record qdrant_unexpected_response metric")
            return []

    def get_collection_info(self) -> Optional[CollectionInfo]:
        """Get information about the memory collection for monitoring.

        Returns:
            Dictionary with collection statistics or None if unavailable

        Example response:
            {
                "name": "long_term_memory",
                "vectors_count": 42,
                "points_count": 42,
                "status": "green"
            }
        """
        try:
            if not self._collection_exists():
                self.logger.debug("📭 Collection does not exist, cannot get info")
                return None

            def _get_info() -> Any:
                return self.client.get_collection(collection_name=QDRANT_COLLECTION_NAME)

            collection_info: Any = self._circuit_breaker.call(_get_info)

            info = {
                "name": QDRANT_COLLECTION_NAME,  # Collection name is not in the response
                "vectors_count": collection_info.vectors_count if hasattr(collection_info, "vectors_count") else 0,
                "points_count": collection_info.points_count if hasattr(collection_info, "points_count") else 0,
                "status": collection_info.status if hasattr(collection_info, "status") else "unknown",
            }

            self.logger.debug(f"📊 Collection info: {info['points_count']} memories, status={info['status']}")
            return info

        except CircuitBreakerError:
            if LOG_CIRCUIT_BREAKER_EVENTS:
                self.logger.error("⚡ Circuit breaker OPEN: Cannot get collection info")
            return None

    def initialize_collection(self) -> bool:
        """Initialize collection on startup if it doesn't exist.

        This method should be called during application startup to ensure
        the collection exists before any memory operations are attempted.

        Returns:
            bool: True if collection exists or was created successfully, False otherwise

        Example:
            >>> store = get_vector_store()
            >>> if store.initialize_collection():
            ...     print("Memory system ready")
            ... else:
            ...     print("Memory system unavailable")
        """
        try:
            if self._collection_exists():
                self.logger.info(f"✅ Collection '{QDRANT_COLLECTION_NAME}' already exists")
                info = self.get_collection_info()
                if info:
                    self.logger.info(f"📊 Current state: {info['points_count']} memories stored")
                # Validate collection vector dimensions on startup
                if not self._validate_collection_vector_dimensions():
                    self.logger.error(
                        "❌ Collection dimension validation failed: the configured vector size does not match the embedding model"
                    )
                return True
            else:
                self.logger.info(f"🏗️ Collection does not exist, creating '{QDRANT_COLLECTION_NAME}'...")
                self._create_collection()
                # Verify creation succeeded
                if self._collection_exists():
                    self.logger.info(f"✅ Collection '{QDRANT_COLLECTION_NAME}' created and verified")
                    return True
                else:
                    self.logger.error("❌ Collection creation verification failed")
                    return False
        except Exception as e:
            self.logger.error(f"❌ Collection initialization failed: {e}")
            return False

    def _extract_vector_size_from_collection_info(self, collection_info: Any) -> Optional[int]:
        """Attempt to extract configured vector size using several possible shapes returned by qdrant-client.

        Qdrant client representations vary slightly between versions. This helper tries a few common
        attribute paths and returns the integer size if found, or None otherwise.
        """
        try:
            # pattern 0: collection_info.result.config.params.vectors.size (Qdrant API raw JSON 'result' shape)
            result = getattr(collection_info, "result", None)
            if result and hasattr(result, "config") and hasattr(result.config, "params"):
                vectors_conf = getattr(result.config.params, "vectors", None)
                if vectors_conf and hasattr(vectors_conf, "size"):
                    return int(vectors_conf.size)

            # pattern 1: collection_info.config.params.vectors.size (qdrant_client v1.12 representation)
            if hasattr(collection_info, "config") and hasattr(collection_info.config, "params"):
                vectors_conf = getattr(collection_info.config.params, "vectors", None)
                if vectors_conf and hasattr(vectors_conf, "size"):
                    return int(vectors_conf.size)

            # pattern 2: collection_info.vectors.params.size
            vectors = getattr(collection_info, "vectors", None)
            if vectors is not None and hasattr(vectors, "params") and hasattr(vectors.params, "size"):
                return int(vectors.params.size)

            # pattern 2: collection_info.params.vectors.size
            params = getattr(collection_info, "params", None)
            if params is not None and hasattr(params, "vectors") and hasattr(params.vectors, "size"):
                return int(params.vectors.size)

            # pattern 3: dictionary-like access (raw JSON returned by the API)
            if isinstance(collection_info, dict):
                vectors_conf = (
                    collection_info.get("vectors")
                    or (collection_info.get("config", {}) or {}).get("params", {}).get("vectors")
                    or collection_info.get("params", {}).get("vectors")
                )
                if isinstance(vectors_conf, dict) and "size" in vectors_conf:
                    return int(vectors_conf["size"])
        except Exception:
            pass
        return None

    def _validate_collection_vector_dimensions(self) -> bool:
        """Validate the collection vector dimensions match expected embedding size.

        Returns:
            bool: True if dimension is as expected or collection doesn't provide size info, False if mismatch.
        """
        try:
            if not self._collection_exists():
                self.logger.debug("📭 Collection does not exist for dimension validation")
                return True

            def _get() -> Any:
                return self.client.get_collection(collection_name=QDRANT_COLLECTION_NAME)

            coll_info = self._circuit_breaker.call(_get)
            # For debugging - log collection_info attributes if we cannot determine vector size
            try:
                self.logger.debug(f"collection_info_dump: {repr(coll_info)[:2000]}")
            except Exception:
                pass
            if not coll_info:
                self.logger.debug("📭 Collection info is unavailable for dimension validation")
                return True

            vector_size = self._extract_vector_size_from_collection_info(coll_info)
            if vector_size is None:
                self.logger.warning(
                    "⚠️ Could not determine collection vector size; skipping strict validation (Qdrant client returned unknown format)"
                )
                return True

            if vector_size != EMBEDDING_VECTOR_DIMENSIONS:
                self.logger.error(
                    "❌ Qdrant collection vector dimension mismatch",
                    expected=EMBEDDING_VECTOR_DIMENSIONS,
                    configured=vector_size,
                    collection=QDRANT_COLLECTION_NAME,
                )
                # Return False to indicate mismatch detected (but do not auto-recreate by default)
                return False

            self.logger.info(
                f"✅ Qdrant collection vector dimension validated: {vector_size} == {EMBEDDING_VECTOR_DIMENSIONS}"
            )
            return True
        except CircuitBreakerError:
            if LOG_CIRCUIT_BREAKER_EVENTS:
                self.logger.warning("⚡ Circuit breaker OPEN: Cannot validate collection dimensions")
            return True
        except Exception as e:
            self.logger.error("❌ Failed to validate collection dimensions", error=str(e))
            return True


@lru_cache
def get_vector_store() -> VectorStore:
    """Get or create the VectorStore singleton instance.

    Uses LRU cache to ensure only one VectorStore instance exists across
    the application. This provides efficient resource management and connection
    pooling for Qdrant operations.

    Returns:
        VectorStore: The singleton VectorStore instance

    Example:
        >>> store1 = get_vector_store()
        >>> store2 = get_vector_store()
        >>> assert store1 is store2  # Same instance
    """
    return VectorStore()
