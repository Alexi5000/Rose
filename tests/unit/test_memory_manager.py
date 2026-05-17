"""Unit tests for Memory Manager module.

Tests memory extraction, storage, retrieval, and formatting operations
with mocked Qdrant vector store.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from ai_companion.modules.memory.long_term.memory_manager import (
    MemoryAnalysis,
    MemoryManager,
)


@pytest.mark.unit
class TestMemoryExtraction:
    """Test memory extraction from HumanMessage."""

    @pytest.mark.asyncio
    async def test_extract_important_memory_from_human_message(self, mock_qdrant_client):
        """Test extracting important information from a human message."""
        # Mock the LLM response
        mock_analysis = MemoryAnalysis(
            is_important=True, formatted_memory="Experiencing anxiety following mother's death one month ago"
        )

        with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_vs:
            mock_vs.return_value.find_similar_memory.return_value = None
            mock_vs.return_value.store_memory = MagicMock()

            manager = MemoryManager()
            manager.llm = AsyncMock()
            manager.llm.ainvoke.return_value = mock_analysis

            message = HumanMessage(content="I've been feeling really anxious since my mom passed away last month")
            await manager.extract_and_store_memories(message)

            # Verify LLM was called with the message
            manager.llm.ainvoke.assert_called_once()
            # Verify memory was stored
            mock_vs.return_value.store_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_skip_non_important_messages(self, mock_qdrant_client):
        """Test that non-important messages are not stored."""
        mock_analysis = MemoryAnalysis(is_important=False, formatted_memory=None)

        with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_vs:
            mock_vs.return_value.store_memory = MagicMock()

            manager = MemoryManager()
            manager.llm = AsyncMock()
            manager.llm.ainvoke.return_value = mock_analysis

            message = HumanMessage(content="Hey, how are you today?")
            await manager.extract_and_store_memories(message)

            # Verify memory was not stored
            mock_vs.return_value.store_memory.assert_not_called()

    @pytest.mark.asyncio
    async def test_ignore_ai_messages(self, mock_qdrant_client):
        """Test that AI messages are ignored for memory extraction."""
        with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store"):
            manager = MemoryManager()
            manager.llm = AsyncMock()

            message = AIMessage(content="I'm here to help you.")
            await manager.extract_and_store_memories(message)

            # Verify LLM was never called
            manager.llm.ainvoke.assert_not_called()

    @pytest.mark.asyncio
    async def test_extract_emotional_state(self, mock_qdrant_client):
        """Test extraction of emotional state information."""
        mock_analysis = MemoryAnalysis(is_important=True, formatted_memory="Experiencing anxiety and sadness")

        with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_vs:
            mock_vs.return_value.find_similar_memory.return_value = None
            mock_vs.return_value.store_memory = MagicMock()

            manager = MemoryManager()
            manager.llm = AsyncMock()
            manager.llm.ainvoke.return_value = mock_analysis

            message = HumanMessage(content="I've been feeling really anxious and sad lately")
            await manager.extract_and_store_memories(message)

            # Verify the formatted memory was stored
            call_args = mock_vs.return_value.store_memory.call_args
            assert call_args[1]["text"] == "Experiencing anxiety and sadness"

    @pytest.mark.asyncio
    async def test_extract_coping_mechanism(self, mock_qdrant_client):
        """Test extraction of coping mechanisms."""
        mock_analysis = MemoryAnalysis(
            is_important=True, formatted_memory="Uses meditation as coping mechanism for grief"
        )

        with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_vs:
            mock_vs.return_value.find_similar_memory.return_value = None
            mock_vs.return_value.store_memory = MagicMock()

            manager = MemoryManager()
            manager.llm = AsyncMock()
            manager.llm.ainvoke.return_value = mock_analysis

            message = HumanMessage(content="Meditation has been helping me cope with the grief")
            await manager.extract_and_store_memories(message)

            call_args = mock_vs.return_value.store_memory.call_args
            assert "meditation" in call_args[1]["text"].lower()


@pytest.mark.unit
class TestMemoryStorage:
    """Test memory storage with duplicate detection."""

    @pytest.mark.asyncio
    async def test_store_new_memory(self, mock_qdrant_client):
        """Test storing a new memory when no duplicate exists."""
        mock_analysis = MemoryAnalysis(is_important=True, formatted_memory="Name is Sarah, lives in Portland")

        with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_vs:
            mock_vs.return_value.find_similar_memory.return_value = None
            mock_vs.return_value.store_memory = MagicMock()

            manager = MemoryManager()
            manager.llm = AsyncMock()
            manager.llm.ainvoke.return_value = mock_analysis

            message = HumanMessage(content="My name is Sarah and I live in Portland")
            await manager.extract_and_store_memories(message)

            # Verify duplicate check was performed (with session_id for multi-user safety)
            mock_vs.return_value.find_similar_memory.assert_called_once_with(
                "Name is Sarah, lives in Portland", session_id=None
            )
            # Verify memory was stored
            mock_vs.return_value.store_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_skip_duplicate_memory(self, mock_qdrant_client):
        """Test that duplicate memories are not stored."""
        mock_analysis = MemoryAnalysis(is_important=True, formatted_memory="Name is Sarah, lives in Portland")

        # Mock a similar memory already exists
        from ai_companion.modules.memory.long_term.vector_store import Memory

        existing_memory = Memory(
            text="Name is Sarah, lives in Portland",
            metadata={"id": "existing_id", "timestamp": "2024-01-01T00:00:00"},
            score=0.95,
        )

        with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_vs:
            mock_vs.return_value.find_similar_memory.return_value = existing_memory
            mock_vs.return_value.store_memory = MagicMock()

            manager = MemoryManager()
            manager.llm = AsyncMock()
            manager.llm.ainvoke.return_value = mock_analysis

            message = HumanMessage(content="My name is Sarah and I live in Portland")
            await manager.extract_and_store_memories(message)

            # Verify duplicate check was performed
            mock_vs.return_value.find_similar_memory.assert_called_once()
            # Verify memory was NOT stored (duplicate detected)
            mock_vs.return_value.store_memory.assert_not_called()

    @pytest.mark.asyncio
    async def test_memory_includes_metadata(self, mock_qdrant_client):
        """Test that stored memories include proper metadata."""
        mock_analysis = MemoryAnalysis(
            is_important=True, formatted_memory="Healing goal: self-forgiveness related to past marriage"
        )

        with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_vs:
            mock_vs.return_value.find_similar_memory.return_value = None
            mock_vs.return_value.store_memory = MagicMock()

            manager = MemoryManager()
            manager.llm = AsyncMock()
            manager.llm.ainvoke.return_value = mock_analysis

            message = HumanMessage(content="I'm working on forgiving myself for the mistakes I made in my marriage")
            await manager.extract_and_store_memories(message)

            # Verify metadata includes id and timestamp
            call_args = mock_vs.return_value.store_memory.call_args
            metadata = call_args[1]["metadata"]
            assert "id" in metadata
            assert "timestamp" in metadata


@pytest.mark.unit
class TestMemoryRetrieval:
    """Test relevant memory retrieval with various contexts."""

    def test_retrieve_relevant_memories(self, mock_qdrant_client):
        """Test retrieving relevant memories based on context."""
        from ai_companion.modules.memory.long_term.vector_store import Memory

        mock_memories = [
            Memory(
                text="Experiencing anxiety following mother's death one month ago",
                metadata={"id": "mem1", "timestamp": "2024-01-15T10:00:00"},
                score=0.92,
            ),
            Memory(
                text="Uses meditation as coping mechanism for grief",
                metadata={"id": "mem2", "timestamp": "2024-01-14T15:00:00"},
                score=0.87,
            ),
        ]

        with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_vs:
            mock_vs.return_value.search_memories.return_value = mock_memories

            manager = MemoryManager()
            memories = manager.get_relevant_memories("I'm having a hard day with my grief")

            # Verify search was called with context
            mock_vs.return_value.search_memories.assert_called_once()
            # Verify memories were returned as text list
            assert len(memories) == 2
            assert memories[0] == "Experiencing anxiety following mother's death one month ago"
            assert memories[1] == "Uses meditation as coping mechanism for grief"

    def test_retrieve_empty_memories_for_new_user(self, mock_qdrant_client):
        """Test handling of empty memory retrieval for new users."""
        with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_vs:
            mock_vs.return_value.search_memories.return_value = []

            manager = MemoryManager()
            memories = manager.get_relevant_memories("Hello, I'm new here")

            # Verify empty list is returned
            assert memories == []

    def test_retrieve_memories_respects_top_k(self, mock_qdrant_client):
        """Test that memory retrieval respects the MEMORY_TOP_K setting."""
        from ai_companion import settings
        from ai_companion.modules.memory.long_term.vector_store import Memory

        mock_memories = [Memory(text=f"Memory {i}", metadata={"id": f"mem{i}"}, score=0.9 - i * 0.1) for i in range(5)]

        with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_vs:
            mock_vs.return_value.search_memories.return_value = mock_memories[:3]

            manager = MemoryManager()
            manager.get_relevant_memories("test context")

            # Verify search was called with correct k value (from settings)
            call_args = mock_vs.return_value.search_memories.call_args
            assert call_args[1]["k"] == settings.settings.MEMORY_TOP_K

    def test_retrieve_grief_related_memories(self, mock_qdrant_client):
        """Test retrieving grief-related memories for therapeutic context."""
        from ai_companion.modules.memory.long_term.vector_store import Memory

        mock_memories = [
            Memory(text="Lost spouse six months ago in car accident", metadata={"id": "mem1"}, score=0.94),
            Memory(text="Experiencing survivor's guilt", metadata={"id": "mem2"}, score=0.89),
        ]

        with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_vs:
            mock_vs.return_value.search_memories.return_value = mock_memories

            manager = MemoryManager()
            memories = manager.get_relevant_memories("I'm struggling with guilt today")

            assert len(memories) == 2
            assert "guilt" in memories[1].lower()


@pytest.mark.unit
class TestMemoryFormatting:
    """Test memory formatting for prompts."""

    def test_format_memories_as_bullet_points(self, mock_qdrant_client):
        """Test formatting memories as bullet points for prompt injection."""
        with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store"):
            manager = MemoryManager()

            memories = [
                "Name is Sarah, lives in Portland",
                "Experiencing anxiety following mother's death",
                "Uses meditation as coping mechanism",
            ]

            formatted = manager.format_memories_for_prompt(memories)

            # Verify bullet point formatting
            assert formatted.startswith("- ")
            assert formatted.count("\n") == 2  # 3 items = 2 newlines
            assert "- Name is Sarah, lives in Portland" in formatted
            assert "- Experiencing anxiety following mother's death" in formatted
            assert "- Uses meditation as coping mechanism" in formatted

    def test_format_empty_memories(self, mock_qdrant_client):
        """Test formatting empty memory list returns empty string."""
        with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store"):
            manager = MemoryManager()

            formatted = manager.format_memories_for_prompt([])

            assert formatted == ""

    def test_format_single_memory(self, mock_qdrant_client):
        """Test formatting a single memory."""
        with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store"):
            manager = MemoryManager()

            memories = ["Name is Emma, grieving loss of partner"]
            formatted = manager.format_memories_for_prompt(memories)

            assert formatted == "- Name is Emma, grieving loss of partner"
            assert "\n" not in formatted  # Single item, no newlines
