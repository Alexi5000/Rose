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

import logging
import uuid
from datetime import datetime
from typing import Any, List, Optional

from langchain_core.messages import BaseMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from ai_companion.core.prompts import MEMORY_ANALYSIS_PROMPT
from ai_companion.modules.memory.long_term.vector_store import VectorStore, get_vector_store
from ai_companion.settings import settings


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

    Attributes:
        vector_store: VectorStore instance for memory persistence
        logger: Logger for memory operations
        llm: Language model configured for memory analysis with structured output

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
            similar = self.vector_store.find_similar_memory(
                analysis.formatted_memory,
                session_id=session_id
            )
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

    def get_relevant_memories(self, context: str, session_id: Optional[str] = None) -> List[str]:
        """Retrieve relevant memories based on the current context.

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
        memories = self.vector_store.search_memories(
            context,
            k=settings.MEMORY_TOP_K,
            session_id=session_id
        )
        # Detailed logging is now handled in vector_store.search_memories()
        return [memory.text for memory in memories]

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


def get_memory_manager() -> MemoryManager:
    """Get a MemoryManager instance.

    Factory function for creating MemoryManager instances. This pattern allows
    for future enhancements like singleton behavior or dependency injection.

    Returns:
        MemoryManager: A new MemoryManager instance

    Example:
        >>> manager = get_memory_manager()
        >>> memories = manager.get_relevant_memories("user preferences")
    """
    return MemoryManager()
