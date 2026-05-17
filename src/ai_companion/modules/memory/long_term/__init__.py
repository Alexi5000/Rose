"""Long-term memory module for AI Companion.

This module provides long-term memory storage and retrieval using Qdrant vector database.
"""

from ai_companion.modules.memory.long_term.memory_manager import MemoryAnalysis, MemoryManager, get_memory_manager
from ai_companion.modules.memory.long_term.vector_store import (
    CollectionInfo,
    Memory,
    MemoryMetadata,
    MemorySearchResult,
    VectorStore,
    get_vector_store,
)

__all__ = [
    # Memory Manager
    "MemoryManager",
    "MemoryAnalysis",
    "get_memory_manager",
    # Vector Store
    "VectorStore",
    "Memory",
    "get_vector_store",
    # Type Aliases
    "MemoryMetadata",
    "MemorySearchResult",
    "CollectionInfo",
]
