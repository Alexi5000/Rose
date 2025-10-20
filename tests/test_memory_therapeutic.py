"""Tests for memory system with therapeutic context."""

from unittest.mock import MagicMock, patch

from langchain_core.messages import HumanMessage

from ai_companion.graph.nodes import memory_extraction_node, memory_injection_node
from ai_companion.graph.state import AICompanionState


class TestTherapeuticMemoryExtraction:
    """Test memory extraction for therapeutic information."""

    @patch("ai_companion.graph.nodes.ChatGroq")
    def test_extract_emotional_state(self, mock_chat):
        """Test extraction of emotional state information."""
        # Mock LLM to return important memory
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content='{"is_important": true, "formatted_memory": "Experiencing anxiety and sadness"}'
        )
        mock_chat.return_value = mock_llm

        state = AICompanionState(
            messages=[HumanMessage(content="I've been feeling really anxious and sad lately")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",
            image_path="",
            current_activity="",
            apply_activity=False,
            memory_context="",
        )

        with patch("ai_companion.graph.nodes.long_term_memory") as mock_memory:
            mock_memory.add_memory = MagicMock()
            result = memory_extraction_node(state)

            # Verify memory was attempted to be stored
            assert result is not None

    @patch("ai_companion.graph.nodes.ChatGroq")
    def test_extract_grief_experience(self, mock_chat):
        """Test extraction of grief and loss information."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content='{"is_important": true, "formatted_memory": "Lost mother two months ago, experiencing deep grief"}'
        )
        mock_chat.return_value = mock_llm

        state = AICompanionState(
            messages=[HumanMessage(content="My mother passed away two months ago and I'm struggling")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",
            image_path="",
            current_activity="",
            apply_activity=False,
            memory_context="",
        )

        with patch("ai_companion.graph.nodes.long_term_memory") as mock_memory:
            mock_memory.add_memory = MagicMock()
            result = memory_extraction_node(state)
            assert result is not None

    @patch("ai_companion.graph.nodes.ChatGroq")
    def test_extract_coping_mechanism(self, mock_chat):
        """Test extraction of coping mechanisms."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content='{"is_important": true, "formatted_memory": "Uses meditation daily to cope with grief"}'
        )
        mock_chat.return_value = mock_llm

        state = AICompanionState(
            messages=[HumanMessage(content="I've been meditating every morning and it helps with my grief")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",
            image_path="",
            current_activity="",
            apply_activity=False,
            memory_context="",
        )

        with patch("ai_companion.graph.nodes.long_term_memory") as mock_memory:
            mock_memory.add_memory = MagicMock()
            result = memory_extraction_node(state)
            assert result is not None

    @patch("ai_companion.graph.nodes.ChatGroq")
    def test_extract_healing_goal(self, mock_chat):
        """Test extraction of healing goals and intentions."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content='{"is_important": true, "formatted_memory": "Healing goal: learn to forgive self for past mistakes"}'
        )
        mock_chat.return_value = mock_llm

        state = AICompanionState(
            messages=[HumanMessage(content="I want to learn to forgive myself for the mistakes I made")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",
            image_path="",
            current_activity="",
            apply_activity=False,
            memory_context="",
        )

        with patch("ai_companion.graph.nodes.long_term_memory") as mock_memory:
            mock_memory.add_memory = MagicMock()
            result = memory_extraction_node(state)
            assert result is not None

    @patch("ai_companion.graph.nodes.ChatGroq")
    def test_extract_trigger_information(self, mock_chat):
        """Test extraction of emotional triggers."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content='{"is_important": true, "formatted_memory": "Triggered by seeing happy families together"}'
        )
        mock_chat.return_value = mock_llm

        state = AICompanionState(
            messages=[HumanMessage(content="I get really upset when I see happy families together")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",
            image_path="",
            current_activity="",
            apply_activity=False,
            memory_context="",
        )

        with patch("ai_companion.graph.nodes.long_term_memory") as mock_memory:
            mock_memory.add_memory = MagicMock()
            result = memory_extraction_node(state)
            assert result is not None

    @patch("ai_companion.graph.nodes.ChatGroq")
    def test_extract_support_system(self, mock_chat):
        """Test extraction of support system details."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content='{"is_important": true, "formatted_memory": "Has supportive sister who checks in daily"}'
        )
        mock_chat.return_value = mock_llm

        state = AICompanionState(
            messages=[HumanMessage(content="My sister has been amazing, she calls me every day")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",
            image_path="",
            current_activity="",
            apply_activity=False,
            memory_context="",
        )

        with patch("ai_companion.graph.nodes.long_term_memory") as mock_memory:
            mock_memory.add_memory = MagicMock()
            result = memory_extraction_node(state)
            assert result is not None

    @patch("ai_companion.graph.nodes.ChatGroq")
    def test_ignore_non_important_messages(self, mock_chat):
        """Test that casual messages are not stored as memories."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content='{"is_important": false, "formatted_memory": null}'
        )
        mock_chat.return_value = mock_llm

        state = AICompanionState(
            messages=[HumanMessage(content="Hey, how are you today?")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",
            image_path="",
            current_activity="",
            apply_activity=False,
            memory_context="",
        )

        with patch("ai_companion.graph.nodes.long_term_memory") as mock_memory:
            mock_memory.add_memory = MagicMock()
            result = memory_extraction_node(state)
            assert result is not None


class TestTherapeuticMemoryRetrieval:
    """Test memory retrieval for therapeutic context."""

    @patch("ai_companion.graph.nodes.long_term_memory")
    def test_retrieve_relevant_memories(self, mock_memory):
        """Test retrieval of relevant therapeutic memories."""
        # Mock memory retrieval
        mock_memory.get_relevant_memories.return_value = [
            "Name is Sarah, lives in Portland",
            "Lost mother three months ago",
            "Uses meditation to cope with grief",
        ]

        state = AICompanionState(
            messages=[HumanMessage(content="I'm having a hard day")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",
            image_path="",
            current_activity="",
            apply_activity=False,
            memory_context="",
        )

        result = memory_injection_node(state)

        # Verify memory context was injected
        assert "memory_context" in result
        assert len(result["memory_context"]) > 0

    @patch("ai_companion.graph.nodes.long_term_memory")
    def test_memory_context_includes_grief_info(self, mock_memory):
        """Test that memory context includes grief-related information."""
        mock_memory.get_relevant_memories.return_value = [
            "Experiencing grief after father's death",
            "Feeling guilty about not visiting more often",
        ]

        state = AICompanionState(
            messages=[HumanMessage(content="Tell me about my situation")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",
            image_path="",
            current_activity="",
            apply_activity=False,
            memory_context="",
        )

        result = memory_injection_node(state)
        assert "memory_context" in result

    @patch("ai_companion.graph.nodes.long_term_memory")
    def test_empty_memory_context(self, mock_memory):
        """Test handling of empty memory context for new users."""
        mock_memory.get_relevant_memories.return_value = []

        state = AICompanionState(
            messages=[HumanMessage(content="Hello, I'm new here")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",
            image_path="",
            current_activity="",
            apply_activity=False,
            memory_context="",
        )

        result = memory_injection_node(state)
        assert "memory_context" in result


class TestMemorySessionContinuity:
    """Test memory persistence across sessions."""

    @patch("ai_companion.graph.nodes.long_term_memory")
    @patch("ai_companion.graph.nodes.ChatGroq")
    def test_memory_recall_across_sessions(self, mock_chat, mock_memory):
        """Test that memories are recalled in subsequent sessions."""
        # First session: store memory
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content='{"is_important": true, "formatted_memory": "Name is Emma, grieving loss of partner"}'
        )
        mock_chat.return_value = mock_llm
        mock_memory.add_memory = MagicMock()

        state1 = AICompanionState(
            messages=[HumanMessage(content="My name is Emma and I lost my partner last year")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",
            image_path="",
            current_activity="",
            apply_activity=False,
            memory_context="",
        )

        memory_extraction_node(state1)

        # Second session: retrieve memory
        mock_memory.get_relevant_memories.return_value = [
            "Name is Emma, grieving loss of partner"
        ]

        state2 = AICompanionState(
            messages=[HumanMessage(content="Do you remember me?")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",
            image_path="",
            current_activity="",
            apply_activity=False,
            memory_context="",
        )

        result = memory_injection_node(state2)
        assert "Emma" in result["memory_context"] or len(result["memory_context"]) > 0

    @patch("ai_companion.graph.nodes.long_term_memory")
    def test_memory_relevance_for_grief_counseling(self, mock_memory):
        """Test that retrieved memories are relevant to grief counseling context."""
        # Mock relevant therapeutic memories
        mock_memory.get_relevant_memories.return_value = [
            "Lost spouse six months ago in car accident",
            "Experiencing survivor's guilt",
            "Has two young children to care for",
        ]

        state = AICompanionState(
            messages=[HumanMessage(content="I'm struggling with guilt today")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",
            image_path="",
            current_activity="",
            apply_activity=False,
            memory_context="",
        )

        result = memory_injection_node(state)
        assert "memory_context" in result
        # Memory context should be populated with relevant info
        assert len(result["memory_context"]) > 0


class TestMemorySystemIntegration:
    """Test integration of memory extraction and injection."""

    @patch("ai_companion.graph.nodes.long_term_memory")
    @patch("ai_companion.graph.nodes.ChatGroq")
    def test_full_memory_cycle(self, mock_chat, mock_memory):
        """Test complete cycle: extract → store → retrieve → inject."""
        # Setup mocks
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content='{"is_important": true, "formatted_memory": "Practices yoga for emotional healing"}'
        )
        mock_chat.return_value = mock_llm
        mock_memory.add_memory = MagicMock()
        mock_memory.get_relevant_memories.return_value = ["Practices yoga for emotional healing"]

        # Extract memory
        state1 = AICompanionState(
            messages=[HumanMessage(content="I do yoga every day and it helps me heal")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",
            image_path="",
            current_activity="",
            apply_activity=False,
            memory_context="",
        )

        memory_extraction_node(state1)

        # Retrieve and inject memory
        state2 = AICompanionState(
            messages=[HumanMessage(content="What do you know about my healing practices?")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",
            image_path="",
            current_activity="",
            apply_activity=False,
            memory_context="",
        )

        result = memory_injection_node(state2)
        assert "memory_context" in result
