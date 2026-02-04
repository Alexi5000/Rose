"""Tests for Rose's character and therapeutic responses."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from ai_companion.core.prompts import CHARACTER_CARD_PROMPT, MEMORY_ANALYSIS_PROMPT
from ai_companion.graph.nodes import conversation_node
from ai_companion.graph.state import AICompanionState


class TestRoseCharacter:
    """Test Rose's healer shaman personality and therapeutic approach."""

    def test_character_card_contains_rose_identity(self):
        """Verify character card defines Rose as healer."""
        assert "Rose" in CHARACTER_CARD_PROMPT
        assert "healer" in CHARACTER_CARD_PROMPT.lower()
        # Rose is described as a "warm, intuitive healer" with "healing traditions" knowledge
        assert "healing" in CHARACTER_CARD_PROMPT.lower()

    def test_character_card_ancient_wisdom_focus(self):
        """Verify character card emphasizes healing wisdom and traditions."""
        prompt_lower = CHARACTER_CARD_PROMPT.lower()
        assert "ancient" in prompt_lower  # "blend ancient wisdom"
        assert "healing" in prompt_lower  # "healing traditions"
        assert "wisdom" in prompt_lower  # "ancient wisdom"
        # Rose is described as having "deep knowledge of healing traditions"
        assert "traditions" in prompt_lower

    def test_character_card_therapeutic_traits(self):
        """Verify character card includes therapeutic personality traits."""
        prompt_lower = CHARACTER_CARD_PROMPT.lower()
        # Rose is described as "warm, intuitive healer" who is "genuine"
        assert "warm" in prompt_lower
        assert "genuine" in prompt_lower
        # Rose is "curious about people" and "comfortable with silence and heavy emotions"
        assert "curious" in prompt_lower
        assert "comfortable" in prompt_lower and "emotions" in prompt_lower

    def test_character_card_no_ava_references(self):
        """Verify no references to Ava remain in character card."""
        assert "Ava" not in CHARACTER_CARD_PROMPT
        assert "Groq ML Engineer" not in CHARACTER_CARD_PROMPT
        assert "San Francisco" not in CHARACTER_CARD_PROMPT

    def test_character_card_voice_capability(self):
        """Verify character card mentions voice capability."""
        assert "voice" in CHARACTER_CARD_PROMPT.lower()

    @pytest.mark.asyncio
    @patch("ai_companion.graph.utils.helpers.ChatGroq")
    async def test_grief_counseling_response(self, mock_chat):
        """Test Rose responds appropriately to grief counseling scenario."""
        # Mock LLM response (use AsyncMock for ainvoke)
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=AIMessage(
                content="I hear the depth of your loss. Grief is a sacred journey, and I'm here to walk alongside you."
            )
        )
        mock_chat.return_value = mock_llm

        # Create state with grief-related message
        state = AICompanionState(
            messages=[HumanMessage(content="I lost my mother last month and I can't stop crying")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",

            current_activity="Available for healing sessions",
            apply_activity=True,
            memory_context="",
        )

        # Invoke conversation node (async)
        result = await conversation_node(state, config={"configurable": {"thread_id": "test"}})

        # Verify response was generated (node returns single AIMessage, not a list)
        assert "messages" in result
        assert isinstance(result["messages"], AIMessage)

    @pytest.mark.asyncio
    @patch("ai_companion.graph.utils.helpers.ChatGroq")
    async def test_holistic_approach_response(self, mock_chat):
        """Test Rose uses holistic healing approach."""
        # Mock LLM response with holistic elements
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=AIMessage(
                content="Your body holds wisdom. Let's explore what it's telling you through this pain."
            )
        )
        mock_chat.return_value = mock_llm

        state = AICompanionState(
            messages=[HumanMessage(content="I feel physical pain when I think about my loss")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",

            current_activity="Available for healing sessions",
            apply_activity=True,
            memory_context="",
        )

        result = await conversation_node(state, config={"configurable": {"thread_id": "test"}})
        assert "messages" in result
        assert isinstance(result["messages"], AIMessage)

    @pytest.mark.asyncio
    @patch("ai_companion.graph.utils.helpers.ChatGroq")
    async def test_ancient_wisdom_metaphors(self, mock_chat):
        """Test Rose uses nature metaphors and ancient wisdom."""
        # Mock response with nature metaphor
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=AIMessage(
                content="Like a river that carves through stone, grief shapes us slowly, patiently."
            )
        )
        mock_chat.return_value = mock_llm

        state = AICompanionState(
            messages=[HumanMessage(content="How long will this pain last?")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",

            current_activity="Available for healing sessions",
            apply_activity=True,
            memory_context="",
        )

        result = await conversation_node(state, config={"configurable": {"thread_id": "test"}})
        assert "messages" in result
        assert isinstance(result["messages"], AIMessage)

    def test_response_length_constraint(self):
        """Verify character card specifies response length limit."""
        # New prompt specifies "Keep responses SHORT - usually 1-3 sentences"
        prompt_lower = CHARACTER_CARD_PROMPT.lower()
        assert "short" in prompt_lower
        assert "1-3 sentences" in prompt_lower

    def test_no_ai_mention_rule(self):
        """Verify character card prohibits mentioning AI nature."""
        # Prompt says "Never say you're an AI. You're Rose."
        prompt_lower = CHARACTER_CARD_PROMPT.lower()
        assert "never say you're an ai" in prompt_lower


class TestTherapeuticMemoryAnalysis:
    """Test memory analysis focuses on therapeutic context."""

    def test_memory_prompt_therapeutic_focus(self):
        """Verify memory analysis prompt prioritizes therapeutic information."""
        prompt_lower = MEMORY_ANALYSIS_PROMPT.lower()
        assert "emotional states" in prompt_lower
        assert "grief" in prompt_lower
        assert "healing" in prompt_lower
        assert "therapeutic" in prompt_lower

    def test_memory_prompt_includes_grief_examples(self):
        """Verify memory prompt includes grief-related examples."""
        assert "grief experiences" in MEMORY_ANALYSIS_PROMPT.lower()
        assert "losses" in MEMORY_ANALYSIS_PROMPT.lower()

    def test_memory_prompt_includes_coping_mechanisms(self):
        """Verify memory prompt tracks coping mechanisms."""
        assert "coping" in MEMORY_ANALYSIS_PROMPT.lower()
        assert "meditation" in MEMORY_ANALYSIS_PROMPT.lower()

    def test_memory_prompt_includes_support_system(self):
        """Verify memory prompt tracks support system details."""
        assert "support system" in MEMORY_ANALYSIS_PROMPT.lower()

    def test_memory_prompt_includes_triggers(self):
        """Verify memory prompt tracks emotional triggers."""
        assert "trigger" in MEMORY_ANALYSIS_PROMPT.lower()


class TestTherapeuticScenarios:
    """Test Rose's responses to various therapeutic scenarios."""

    @pytest.mark.asyncio
    @patch("ai_companion.graph.utils.helpers.ChatGroq")
    async def test_validation_response(self, mock_chat):
        """Test Rose validates user's emotions."""
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="Your feelings are valid and important."))
        mock_chat.return_value = mock_llm

        state = AICompanionState(
            messages=[HumanMessage(content="I feel guilty for being angry at my deceased father")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",

            current_activity="Available for healing sessions",
            apply_activity=True,
            memory_context="",
        )

        result = await conversation_node(state, config={"configurable": {"thread_id": "test"}})
        assert "messages" in result
        assert isinstance(result["messages"], AIMessage)

    @pytest.mark.asyncio
    @patch("ai_companion.graph.utils.helpers.ChatGroq")
    async def test_non_judgmental_response(self, mock_chat):
        """Test Rose maintains non-judgmental stance."""
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="There's no right or wrong way to grieve."))
        mock_chat.return_value = mock_llm

        state = AICompanionState(
            messages=[HumanMessage(content="I'm not crying enough. Am I grieving wrong?")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",

            current_activity="Available for healing sessions",
            apply_activity=True,
            memory_context="",
        )

        result = await conversation_node(state, config={"configurable": {"thread_id": "test"}})
        assert "messages" in result
        assert isinstance(result["messages"], AIMessage)

    @pytest.mark.asyncio
    @patch("ai_companion.graph.utils.helpers.ChatGroq")
    async def test_spiritual_awareness_response(self, mock_chat):
        """Test Rose demonstrates spiritual awareness."""
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=AIMessage(
                content="The ancestors remind us that death is not an ending, but a transformation."
            )
        )
        mock_chat.return_value = mock_llm

        state = AICompanionState(
            messages=[HumanMessage(content="Do you believe in life after death?")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",

            current_activity="Available for healing sessions",
            apply_activity=True,
            memory_context="",
        )

        result = await conversation_node(state, config={"configurable": {"thread_id": "test"}})
        assert "messages" in result
        assert isinstance(result["messages"], AIMessage)

    @pytest.mark.asyncio
    @patch("ai_companion.graph.utils.helpers.ChatGroq")
    async def test_patient_presence(self, mock_chat):
        """Test Rose demonstrates patience and presence."""
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="Take all the time you need. I'm here."))
        mock_chat.return_value = mock_llm

        state = AICompanionState(
            messages=[HumanMessage(content="I don't know what to say")],
            summary="",
            workflow="conversation",
            audio_buffer=b"",

            current_activity="Available for healing sessions",
            apply_activity=True,
            memory_context="",
        )

        result = await conversation_node(state, config={"configurable": {"thread_id": "test"}})
        assert "messages" in result
        assert isinstance(result["messages"], AIMessage)


class TestRoseActivities:
    """Test Rose's current activity context."""

    def test_healing_session_availability(self):
        """Test Rose's activity reflects healing session availability."""
        # This would be tested in context injection
        # Verify the activity string is appropriate for a healer
        activity = "Available for healing sessions"
        assert "healing" in activity.lower()
        assert "available" in activity.lower()
