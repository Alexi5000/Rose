import os
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import List, Optional

from ai_companion.core.resilience import get_qdrant_circuit_breaker, CircuitBreakerError
from ai_companion.settings import settings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer


@dataclass
class Memory:
    """Represents a memory entry in the vector store."""

    text: str
    metadata: dict
    score: Optional[float] = None

    @property
    def id(self) -> Optional[str]:
        return self.metadata.get("id")

    @property
    def timestamp(self) -> Optional[datetime]:
        ts = self.metadata.get("timestamp")
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
            self.model = SentenceTransformer(self.EMBEDDING_MODEL)
            # Qdrant client maintains internal connection pooling
            self.client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
            self._circuit_breaker = get_qdrant_circuit_breaker()
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
        """Find if a similar memory already exists.

        Args:
            text: The text to search for

        Returns:
            Optional Memory if a similar one is found
        """
        results = self.search_memories(text, k=1)
        if results and results[0].score >= self.SIMILARITY_THRESHOLD:
            return results[0]
        return None

    def store_memory(self, text: str, metadata: dict) -> None:
        """Store a new memory in the vector store or update if similar exists.

        Args:
            text: The text content of the memory
            metadata: Additional information about the memory (timestamp, type, etc.)
        """
        try:
            if not self._collection_exists():
                self._create_collection()

            # Check if similar memory exists
            similar_memory = self.find_similar_memory(text)
            if similar_memory and similar_memory.id:
                metadata["id"] = similar_memory.id  # Keep same ID for update

            embedding = self.model.encode(text)
            point = PointStruct(
                id=metadata.get("id", hash(text)),
                vector=embedding.tolist(),
                payload={
                    "text": text,
                    **metadata,
                },
            )

            def _upsert():
                return self.client.upsert(
                    collection_name=self.COLLECTION_NAME,
                    points=[point],
                )

            self._circuit_breaker.call(_upsert)

        except CircuitBreakerError:
            # Circuit breaker is open - log and continue without storing
            import logging

            logging.getLogger(__name__).error(
                f"Cannot store memory in Qdrant: circuit breaker is open. Memory: {text[:50]}..."
            )

    def search_memories(self, query: str, k: int = 5) -> List[Memory]:
        """Search for similar memories in the vector store.

        Args:
            query: Text to search for
            k: Number of results to return

        Returns:
            List of Memory objects
        """
        try:
            if not self._collection_exists():
                return []

            query_embedding = self.model.encode(query)

            def _search():
                return self.client.search(
                    collection_name=self.COLLECTION_NAME,
                    query_vector=query_embedding.tolist(),
                    limit=k,
                )

            results = self._circuit_breaker.call(_search)

            return [
                Memory(
                    text=hit.payload["text"],
                    metadata={k: v for k, v in hit.payload.items() if k != "text"},
                    score=hit.score,
                )
                for hit in results
            ]

        except CircuitBreakerError:
            # Circuit breaker is open - return empty list
            import logging

            logging.getLogger(__name__).error("Cannot search Qdrant memories: circuit breaker is open")
            return []


@lru_cache
def get_vector_store() -> VectorStore:
    """Get or create the VectorStore singleton instance."""
    return VectorStore()
