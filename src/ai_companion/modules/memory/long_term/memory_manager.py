"""Long-term memory management for the AI companion.

This module provides the MemoryManager class which handles extraction, storage,
and retrieval of important information from conversations. It uses an LLM to
analyze messages for importance and formats them for storage in a vector database.

The memory system enables the AI companion to remember user preferences, past
conversations, and important context across sessions, creating a more personalized
and therapeutic experience.

Module Dependencies:
- ai_companion.core.prompts: MEMORY_ANALYSIS_PROMPT for LLM-based memory extraction
- ai_companion.modules.memory.long_term.vector_store: VectorStore for memory persistence
- ai_companion.settings: Configuration for LLM model, temperature, timeouts
- langchain_core.messages: BaseMessage types for message handling
- langchain_groq: ChatGroq for LLM inference
- pydantic: BaseModel for structured output (MemoryAnalysis)
- Standard library: logging, uuid, datetime, typing

Dependents (modules that import this):
- ai_companion.graph.nodes: memory_extraction_node, memory_injection_node
- Test modules: tests/unit/test_memory_manager.py

Architecture:
This module is part of the modules layer and orchestrates memory operations by
combining LLM analysis (via Groq) with vector storage (via Qdrant). It follows
the factory pattern for instantiation (get_memory_manager) to support dependency
injection and testing.

For detailed architecture documentation, see:
- docs/ARCHITECTURE.md: Memory System Architecture section
- docs/ARCHITECTURE.md: Module Initialization Patterns section (Factory Functions)

Design Reference:
- .kiro/specs/technical-debt-management/design.md: Type Safety Enhancement section

Example:
    Basic usage of the memory manager:

    >>> manager = get_memory_manager()
    >>> message = HumanMessage(content="I love hiking in the mountains")
    >>> await manager.extract_and_store_memories(message)
    >>> memories = manager.get_relevant_memories("outdoor activities")
    >>> print(memories)
    ['User enjoys hiking in mountainous terrain']
"""

import hashlib
import logging
import uuid
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.messages import BaseMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from ai_companion.core.prompts import MEMORY_ANALYSIS_PROMPT
from ai_companion.modules.memory.long_term.vector_store import VectorStore, get_vector_store
from ai_companion.settings import settings

# Phase 3: Memory search cache configuration
MEMORY_CACHE_TTL_SECONDS = 60  # Cache search results for 1 minute
MEMORY_CACHE_MAX_SIZE = 100  # Maximum number of cached search results


class MemoryAnalysis(BaseModel):
    """Result of analyzing a message for memory-worthy content."""

    is_important: bool = Field(
        ...,
        description="Whether the message is important enough to be stored as a memory",
    )
    formatted_memory: Optional[str] = Field(..., description="The formatted memory to be stored")


class MemoryManager:
    """Manager class for handling long-term memory operations.

    This class orchestrates the memory lifecycle: analyzing messages for importance,
    formatting them for storage, checking for duplicates, and retrieving relevant
    memories based on conversation context.

    The manager uses a small LLM (configured via settings) to analyze messages and
    determine what information is worth remembering. It then stores memories in a
    vector database for semantic search and retrieval.

    Phase 3 Optimization: Includes search result caching to reduce Qdrant query
    latency for repeated or similar queries within the same session.

    Attributes:
        vector_store: VectorStore instance for memory persistence
        logger: Logger for memory operations
        llm: Language model configured for memory analysis with structured output
        _search_cache: LRU-style cache for search results

    Example:
        >>> manager = MemoryManager()
        >>> message = HumanMessage(content="My birthday is June 15th")
        >>> await manager.extract_and_store_memories(message)
        >>> memories = manager.get_relevant_memories("when is the user's birthday")
        >>> formatted = manager.format_memories_for_prompt(memories)
    """

    def __init__(self) -> None:
        """Initialize the MemoryManager with vector store and LLM.

        The LLM is configured with structured output to return MemoryAnalysis
        objects that indicate whether a message is important and how to format it.
        """
        self.vector_store: VectorStore = get_vector_store()
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.llm: Any = ChatGroq(  # type: ignore[call-arg]  # ChatGroq API accepts api_key as string, type stubs may be outdated
            model=settings.SMALL_TEXT_MODEL_NAME,
            api_key=settings.GROQ_API_KEY,
            temperature=settings.LLM_TEMPERATURE_MEMORY,
            timeout=settings.LLM_TIMEOUT_SECONDS,
            max_retries=settings.LLM_MAX_RETRIES,
        ).with_structured_output(MemoryAnalysis)
        
        # Phase 3: Search result caching for reduced Qdrant query latency
        # Cache key: hash of (context, session_id), value: (memories, timestamp)
        self._search_cache: Dict[str, Tuple[List[str], datetime]] = {}

    async def _analyze_memory(self, message: str) -> MemoryAnalysis:
        """Analyze a message to determine importance and format if needed.

        Uses an LLM to evaluate whether the message contains information worth
        storing as a long-term memory. If important, the LLM also formats the
        memory in a concise, searchable form.

        Args:
            message: The message content to analyze

        Returns:
            MemoryAnalysis: Contains is_important flag and formatted_memory text

        Example:
            >>> analysis = await manager._analyze_memory("I prefer tea over coffee")
            >>> if analysis.is_important:
            ...     print(analysis.formatted_memory)
            'User prefers tea to coffee'
        """
        prompt = MEMORY_ANALYSIS_PROMPT.format(message=message)
        return await self.llm.ainvoke(prompt)

    async def extract_and_store_memories(self, message: BaseMessage, session_id: Optional[str] = None) -> None:
        """Extract important information from a message and store in vector store.

        This method processes human messages to identify and store important information.
        It performs the following steps:
        1. Analyzes the message using an LLM to determine importance
        2. Checks for duplicate or similar existing memories within the session
        3. Stores new memories with metadata (ID, timestamp, session_id)

        Only human messages are processed; AI messages are ignored to avoid storing
        the companion's own responses.

        Args:
            message: The message to analyze (only HumanMessage types are processed)
            session_id: Optional session/user identifier for multi-user isolation

        Returns:
            None: Memories are stored as a side effect

        Example:
            >>> message = HumanMessage(content="I'm allergic to peanuts")
            >>> await manager.extract_and_store_memories(message, session_id="user_123")
            # Logs: "💾 Storing new memory: 'User has peanut allergy'"
        """
        if message.type != "human":
            return

        # 🧠 Analyze the message for importance and formatting
        # The LLM determines if the message contains information worth remembering
        # and formats it in a concise, searchable form (e.g., "User prefers tea")
        analysis = await self._analyze_memory(message.content)
        if analysis.is_important and analysis.formatted_memory:
            # ♻️ Check if similar memory exists (within the same session)
            # This prevents duplicate storage of the same information
            similar = self.vector_store.find_similar_memory(analysis.formatted_memory, session_id=session_id)
            if similar:
                # Skip storage if we already have a similar memory
                self.logger.info(f"♻️ Similar memory exists, skipping: '{analysis.formatted_memory}'")
                return

            # 💾 Store new memory with unique ID, timestamp, and session_id
            self.logger.info(f"💾 Storing new memory: '{analysis.formatted_memory}'")
            self.vector_store.store_memory(
                text=analysis.formatted_memory,
                metadata={
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat(),
                },
                session_id=session_id,
            )
            
            # Invalidate cache to ensure fresh results include the new memory
            self.invalidate_cache(session_id=session_id)

    def _get_cache_key(self, context: str, session_id: Optional[str]) -> str:
        """Generate a cache key for memory search results.
        
        Args:
            context: Search context
            session_id: Session identifier
            
        Returns:
            str: SHA256 hash of the combined key
        """
        cache_input = f"{context}|{session_id or 'default'}|{settings.MEMORY_TOP_K}"
        return hashlib.sha256(cache_input.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[List[str]]:
        """Retrieve cached search results if available and not expired.
        
        Args:
            cache_key: Cache key to look up
            
        Returns:
            Optional[List[str]]: Cached memories or None if not found/expired
        """
        if cache_key in self._search_cache:
            memories, timestamp = self._search_cache[cache_key]
            age = datetime.now() - timestamp
            if age < timedelta(seconds=MEMORY_CACHE_TTL_SECONDS):
                self.logger.debug(f"📦 Memory cache hit: {cache_key[:16]}... (age: {age.total_seconds():.1f}s)")
                return memories
            else:
                # Expired - remove from cache
                del self._search_cache[cache_key]
                self.logger.debug(f"📦 Memory cache expired: {cache_key[:16]}...")
        return None
    
    def _add_to_cache(self, cache_key: str, memories: List[str]) -> None:
        """Add search results to cache with LRU eviction.
        
        Args:
            cache_key: Cache key
            memories: List of memory texts to cache
        """
        # LRU-style eviction: remove oldest entries if cache is full
        if len(self._search_cache) >= MEMORY_CACHE_MAX_SIZE:
            # Find and remove the oldest entry
            oldest_key = min(
                self._search_cache.keys(),
                key=lambda k: self._search_cache[k][1]
            )
            del self._search_cache[oldest_key]
            self.logger.debug(f"📦 Memory cache evicted: {oldest_key[:16]}...")
        
        self._search_cache[cache_key] = (memories, datetime.now())
        self.logger.debug(f"📦 Memory cached: {cache_key[:16]}... ({len(memories)} memories)")
    
    def invalidate_cache(self, session_id: Optional[str] = None) -> None:
        """Invalidate cache entries, optionally filtered by session.
        
        Called after storing new memories to ensure fresh results on next retrieval.
        
        Args:
            session_id: If provided, only invalidate entries for this session
        """
        if session_id is None:
            count = len(self._search_cache)
            self._search_cache.clear()
            self.logger.debug(f"📦 Memory cache cleared: {count} entries")
        else:
            # Invalidate entries that might be affected by this session
            # Since we hash the key, we can't easily filter - clear all for safety
            count = len(self._search_cache)
            self._search_cache.clear()
            self.logger.debug(f"📦 Memory cache cleared for session update: {count} entries")

    def get_relevant_memories(self, context: str, session_id: Optional[str] = None) -> List[str]:
        """Retrieve relevant memories based on the current context.

        Phase 3 Optimization: Results are cached for MEMORY_CACHE_TTL_SECONDS to
        reduce repeated Qdrant queries during a conversation turn.

        Performs semantic search in the vector store to find memories that are
        relevant to the given context. Returns the top-K most similar memories
        (K is configured via settings.MEMORY_TOP_K).

        If session_id is provided and ENABLE_SESSION_ISOLATION is True, only
        memories from that session are retrieved (prevents cross-user data leakage).

        Args:
            context: The current conversation context to search against
            session_id: Optional session/user identifier for filtering

        Returns:
            List[str]: List of relevant memory texts, ordered by relevance

        Example:
            >>> context = "What outdoor activities do I enjoy?"
            >>> memories = manager.get_relevant_memories(context, session_id="user_123")
            >>> print(memories)
            ['User enjoys hiking in mountainous terrain', 'User likes camping']
        """
        # Check cache first
        cache_key = self._get_cache_key(context, session_id)
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Cache miss - query vector store
        memories = self.vector_store.search_memories(context, k=settings.MEMORY_TOP_K, session_id=session_id)

        # Phase 5: Sort by temporal score (recent memories weighted higher)
        # This ensures fresh memories are prioritized over stale ones
        memories_sorted = sorted(memories, key=lambda m: m.temporal_score, reverse=True)
        
        # Log temporal scoring for debugging
        if memories_sorted:
            self.logger.debug(
                f"⏱️ Temporal scoring applied: "
                f"{[f'{m.text[:30]}... (age: {m.age_days:.1f}d, score: {m.temporal_score:.2f})' for m in memories_sorted[:3]]}"
            )
        
        memory_texts = [memory.text for memory in memories_sorted]
        
        # Add to cache
        self._add_to_cache(cache_key, memory_texts)
        
        return memory_texts

    def format_memories_for_prompt(self, memories: List[str]) -> str:
        """Format retrieved memories as bullet points for inclusion in prompts.

        Converts a list of memory strings into a formatted bullet-point list
        suitable for injection into the character card or system prompt.

        Args:
            memories: List of memory texts to format

        Returns:
            str: Formatted string with bullet points, or empty string if no memories

        Example:
            >>> memories = ['User enjoys hiking', 'User prefers tea']
            >>> formatted = manager.format_memories_for_prompt(memories)
            >>> print(formatted)
            - User enjoys hiking
            - User prefers tea
        """
        if not memories:
            return ""
        return "\n".join(f"- {memory}" for memory in memories)


@lru_cache(maxsize=1)
def get_memory_manager() -> MemoryManager:
    """Get the singleton MemoryManager instance.

    Returns a cached singleton so the search cache persists across requests
    and the LLM/VectorStore connections are reused.

    Returns:
        MemoryManager: The singleton MemoryManager instance
    """
    return MemoryManager()
