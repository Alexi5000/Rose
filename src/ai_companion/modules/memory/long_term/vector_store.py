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

import os
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

from ai_companion.core.resilience import CircuitBreaker, CircuitBreakerError, get_qdrant_circuit_breaker
from ai_companion.settings import settings

# Type aliases for common memory types
MemoryMetadata = Dict[str, Any]
MemorySearchResult = List["Memory"]
CollectionInfo = Dict[str, Any]


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
    """

    REQUIRED_ENV_VARS = ["QDRANT_URL", "QDRANT_API_KEY"]
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    COLLECTION_NAME = "long_term_memory"
    SIMILARITY_THRESHOLD = 0.9  # Threshold for considering memories as similar

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
        """
        if not self._initialized:
            self._validate_env_vars()
            self.model: SentenceTransformer = SentenceTransformer(self.EMBEDDING_MODEL)
            # Qdrant client maintains internal connection pooling
            self.client: QdrantClient = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
            self._circuit_breaker: CircuitBreaker = get_qdrant_circuit_breaker()
            VectorStore._initialized = True

    def _validate_env_vars(self) -> None:
        """Validate that all required environment variables are set."""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    def _collection_exists(self) -> bool:
        """Check if the memory collection exists."""
        try:
            collections = self._circuit_breaker.call(self.client.get_collections).collections
            return any(col.name == self.COLLECTION_NAME for col in collections)
        except CircuitBreakerError:
            # Circuit breaker is open - assume collection doesn't exist
            return False

    def _create_collection(self) -> None:
        """Create a new collection for storing memories."""
        sample_embedding = self.model.encode("sample text")

        def _create():
            return self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=len(sample_embedding),
                    distance=Distance.COSINE,
                ),
            )

        try:
            self._circuit_breaker.call(_create)
        except CircuitBreakerError:
            # Circuit breaker is open - log and continue
            import logging

            logging.getLogger(__name__).error("Cannot create Qdrant collection: circuit breaker is open")

    def find_similar_memory(self, text: str) -> Optional[Memory]:
        """Find if a similar memory already exists to prevent duplicates.

        Searches for memories with similarity score >= SIMILARITY_THRESHOLD (0.9).
        This high threshold ensures only near-duplicate memories are detected,
        allowing for variations in phrasing while preventing redundant storage.

        Args:
            text: The text to search for similar memories

        Returns:
            Optional[Memory]: The most similar memory if found above threshold,
                            None otherwise

        Example:
            >>> similar = store.find_similar_memory("User likes coffee")
            >>> if similar:
            ...     print(f"Found similar: {similar.text}")
            Found similar: User prefers coffee over tea
        """
        results = self.search_memories(text, k=1)
        if results and results[0].score >= self.SIMILARITY_THRESHOLD:
            return results[0]
        return None

    def store_memory(self, text: str, metadata: MemoryMetadata) -> None:
        """Store a new memory in the vector store or update if similar exists.

        This method performs the following operations:
        1. Creates the collection if it doesn't exist
        2. Checks for similar existing memories (similarity >= 0.9)
        3. If similar memory found, updates it (keeps same ID)
        4. If new memory, generates embedding and stores with metadata

        Circuit breaker protection ensures graceful handling of Qdrant unavailability.
        If the circuit breaker is open, the operation is logged and skipped without
        raising an exception.

        Args:
            text: The text content of the memory to store
            metadata: Additional information about the memory (id, timestamp, etc.)
                     Must include 'id' and 'timestamp' keys

        Returns:
            None: Memory is stored as a side effect

        Raises:
            No exceptions are raised; errors are logged internally

        Example:
            >>> store.store_memory(
            ...     text="User has a cat named Whiskers",
            ...     metadata={"id": "mem_456", "timestamp": "2025-01-15T14:30:00"}
            ... )
        """
        try:
            if not self._collection_exists():
                self._create_collection()

            # Check if similar memory exists (prevents duplicates)
            # If found, we update the existing memory by reusing its ID
            similar_memory: Optional[Memory] = self.find_similar_memory(text)
            if similar_memory and similar_memory.id:
                metadata["id"] = similar_memory.id  # Keep same ID for update

            # Generate embedding using sentence transformer model
            embedding: Any = self.model.encode(text)
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
                    collection_name=self.COLLECTION_NAME,
                    points=[point],
                )

            self._circuit_breaker.call(_upsert)

        except CircuitBreakerError:
            # Circuit breaker is open - log and continue without storing
            # This prevents cascading failures when Qdrant is unavailable
            import logging

            logging.getLogger(__name__).error(
                f"Cannot store memory in Qdrant: circuit breaker is open. Memory: {text[:50]}..."
            )

    def search_memories(self, query: str, k: int = 5) -> MemorySearchResult:
        """Search for similar memories in the vector store using semantic search.

        Performs cosine similarity search on memory embeddings to find the most
        relevant memories for the given query. Results are ordered by similarity
        score (higher is more similar).

        Circuit breaker protection ensures graceful handling of Qdrant unavailability.
        If the circuit breaker is open, an empty list is returned.

        Args:
            query: Text to search for (will be embedded for similarity comparison)
            k: Number of results to return (default: 5)

        Returns:
            List[Memory]: List of Memory objects ordered by relevance (highest score first)
                         Returns empty list if collection doesn't exist or circuit breaker is open

        Example:
            >>> results = store.search_memories("user's dietary restrictions", k=3)
            >>> for memory in results:
            ...     print(f"{memory.text} (score: {memory.score:.2f})")
            User is allergic to peanuts (score: 0.92)
            User follows vegetarian diet (score: 0.85)
            User avoids gluten (score: 0.78)
        """
        try:
            if not self._collection_exists():
                return []

            # Generate embedding for the query using the same model as storage
            query_embedding: Any = self.model.encode(query)

            def _search() -> List[Any]:
                return self.client.search(
                    collection_name=self.COLLECTION_NAME,
                    query_vector=query_embedding.tolist(),
                    limit=k,
                )

            results: List[Any] = self._circuit_breaker.call(_search)

            # Convert Qdrant results to Memory objects
            return [
                Memory(
                    text=hit.payload["text"],
                    metadata={k: v for k, v in hit.payload.items() if k != "text"},
                    score=hit.score,
                )
                for hit in results
            ]

        except CircuitBreakerError:
            # Circuit breaker is open - return empty list gracefully
            # This allows the application to continue without memories
            import logging

            logging.getLogger(__name__).error("Cannot search Qdrant memories: circuit breaker is open")
            return []

    def get_collection_info(self) -> Optional[CollectionInfo]:
        """Get information about the memory collection for monitoring.

        Returns:
            Dictionary with collection statistics or None if unavailable
        """
        try:
            if not self._collection_exists():
                return None

            def _get_info() -> Any:
                return self.client.get_collection(collection_name=self.COLLECTION_NAME)

            collection_info: Any = self._circuit_breaker.call(_get_info)

            return {
                "name": collection_info.name,
                "vectors_count": collection_info.vectors_count,
                "points_count": collection_info.points_count,
                "status": collection_info.status,
            }

        except CircuitBreakerError:
            import logging

            logging.getLogger(__name__).error("Cannot get Qdrant collection info: circuit breaker is open")
            return None


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
