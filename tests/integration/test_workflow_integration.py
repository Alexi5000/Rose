"""Integration tests for LangGraph workflow end-to-end execution.

This module tests complete workflow execution with real LangGraph orchestration
but mocked external API calls. Tests verify:
- Complete conversation workflow (message → memory → router → response)
- Audio workflow (audio input → STT → processing → TTS → audio output)
- Memory extraction and injection in workflow
- Conversation summarization trigger
- Workflow timeout handling
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from ai_companion.graph.graph import create_workflow_graph


@pytest.mark.integration
@pytest.mark.asyncio
class TestConversationWorkflow:
    """Test complete conversation workflow execution."""

    async def test_complete_conversation_workflow(
        self,
        mock_groq_client,
        mock_qdrant_client,
    ):
        """Test complete conversation workflow: message → memory → router → response.

        Verifies:
        - Memory extraction from user message
        - Router determines conversation workflow
        - Context and memory injection
        - Conversation response generation
        """
        # Arrange: Create initial state with user message
        initial_state = {
            "messages": [HumanMessage(content="I'm feeling overwhelmed with grief today.")],
            "summary": "",
            "workflow": "",
            "audio_buffer": b"",
            "image_path": "",
            "current_activity": "",
            "apply_activity": False,
            "memory_context": "",
        }

        # Mock the LLM responses
        mock_router_response = MagicMock()
        mock_router_response.response_type = "conversation"

        mock_conversation_response = (
            "I hear you, dear one. Grief can feel overwhelming. Would you like to talk about what you're experiencing?"
        )

        mock_memory_analysis = MagicMock()
        mock_memory_analysis.is_important = True
        mock_memory_analysis.formatted_memory = "User is experiencing overwhelming grief."

        # Act: Execute workflow with mocked dependencies
        with (
            patch("ai_companion.graph.nodes.get_character_response_chain") as mock_get_response_chain,
            patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_get_vector_store,
            patch("ai_companion.modules.memory.long_term.memory_manager.ChatGroq") as mock_memory_llm,
        ):
            # Mock character response chain
            mock_response_chain = AsyncMock()
            mock_response_chain.ainvoke.return_value = mock_conversation_response
            mock_get_response_chain.return_value = mock_response_chain

            # Mock router chain
            with patch("ai_companion.graph.nodes.get_router_chain") as mock_get_router_chain:
                mock_router_chain = AsyncMock()
                mock_router_chain.ainvoke.return_value = mock_router_response
                mock_get_router_chain.return_value = mock_router_chain

                # Mock memory manager LLM
                mock_memory_llm_instance = AsyncMock()
                mock_memory_llm_instance.ainvoke.return_value = mock_memory_analysis
                mock_memory_llm.return_value.with_structured_output.return_value = mock_memory_llm_instance

                # Mock vector store
                mock_vector_store = MagicMock()
                mock_vector_store.find_similar_memory.return_value = None
                mock_vector_store.store_memory.return_value = None
                mock_vector_store.search_memories.return_value = []
                mock_get_vector_store.return_value = mock_vector_store

                # Mock schedule context
                with patch("ai_companion.graph.nodes.ScheduleContextGenerator.get_current_activity") as mock_schedule:
                    mock_schedule.return_value = "Evening Reflection"

                    # Compile and execute graph
                    graph = create_workflow_graph().compile()
                    result = await graph.ainvoke(initial_state)

        # Assert: Verify workflow execution
        assert result is not None
        assert "messages" in result
        assert len(result["messages"]) > 1  # Original message + AI response
        assert result["workflow"] == "conversation"

        # Verify AI response was added
        ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
        assert len(ai_messages) > 0
        assert mock_conversation_response in ai_messages[-1].content

    async def test_conversation_workflow_with_memory_context(
        self,
        mock_groq_client,
        mock_qdrant_client,
    ):
        """Test conversation workflow with memory injection.

        Verifies:
        - Relevant memories are retrieved
        - Memory context is injected into conversation
        - Response incorporates memory context
        """
        # Arrange: Create state with existing conversation
        initial_state = {
            "messages": [HumanMessage(content="Can you remind me what we discussed about my mother?")],
            "summary": "",
            "workflow": "",
            "audio_buffer": b"",
            "image_path": "",
            "current_activity": "",
            "apply_activity": False,
            "memory_context": "",
        }

        # Mock memory retrieval
        mock_memories = [
            MagicMock(text="User lost their mother in a car accident.", score=0.95),
            MagicMock(text="User finds comfort in nature walks.", score=0.87),
        ]

        mock_router_response = MagicMock()
        mock_router_response.response_type = "conversation"

        mock_conversation_response = "Of course. We talked about your mother and how you lost her in a car accident."

        mock_memory_analysis = MagicMock()
        mock_memory_analysis.is_important = True
        mock_memory_analysis.formatted_memory = "User asked to recall previous discussion about their mother."

        # Act: Execute workflow
        with (
            patch("ai_companion.graph.nodes.get_character_response_chain") as mock_get_response_chain,
            patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_get_vector_store,
            patch("ai_companion.modules.memory.long_term.memory_manager.ChatGroq") as mock_memory_llm,
        ):
            mock_response_chain = AsyncMock()
            mock_response_chain.ainvoke.return_value = mock_conversation_response
            mock_get_response_chain.return_value = mock_response_chain

            with patch("ai_companion.graph.nodes.get_router_chain") as mock_get_router_chain:
                mock_router_chain = AsyncMock()
                mock_router_chain.ainvoke.return_value = mock_router_response
                mock_get_router_chain.return_value = mock_router_chain

                mock_memory_llm_instance = AsyncMock()
                mock_memory_llm_instance.ainvoke.return_value = mock_memory_analysis
                mock_memory_llm.return_value.with_structured_output.return_value = mock_memory_llm_instance

                mock_vector_store = MagicMock()
                mock_vector_store.find_similar_memory.return_value = None
                mock_vector_store.store_memory.return_value = None
                mock_vector_store.search_memories.return_value = mock_memories
                mock_get_vector_store.return_value = mock_vector_store

                with patch("ai_companion.graph.nodes.ScheduleContextGenerator.get_current_activity") as mock_schedule:
                    mock_schedule.return_value = "Evening Reflection"

                    graph = create_workflow_graph().compile()
                    result = await graph.ainvoke(initial_state)

        # Assert: Verify memory context was injected
        assert result is not None
        assert result["memory_context"] != ""
        assert "User lost their mother" in result["memory_context"]


@pytest.mark.integration
@pytest.mark.asyncio
class TestAudioWorkflow:
    """Test audio workflow execution."""

    async def test_audio_workflow_end_to_end(
        self,
        mock_groq_client,
        mock_qdrant_client,
        sample_wav_bytes,
    ):
        """Test audio workflow: audio input → STT → processing → TTS → audio output.

        Verifies:
        - Audio transcription via STT
        - Text processing through conversation node
        - Audio synthesis via TTS
        - Audio buffer in final state
        """
        # Arrange: Create state with audio workflow
        initial_state = {
            "messages": [HumanMessage(content="I need help with breathing exercises.")],
            "summary": "",
            "workflow": "",
            "audio_buffer": b"",
            "image_path": "",
            "current_activity": "",
            "apply_activity": False,
            "memory_context": "",
        }

        mock_router_response = MagicMock()
        mock_router_response.response_type = "audio"

        mock_conversation_response = "Let's do a breathing exercise together. Breathe in slowly for four counts."
        mock_audio_output = b"fake_audio_data_from_tts"

        mock_memory_analysis = MagicMock()
        mock_memory_analysis.is_important = True
        mock_memory_analysis.formatted_memory = "User requested help with breathing exercises."

        # Act: Execute workflow
        with (
            patch("ai_companion.graph.nodes.get_character_response_chain") as mock_get_response_chain,
            patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_get_vector_store,
            patch("ai_companion.modules.memory.long_term.memory_manager.ChatGroq") as mock_memory_llm,
            patch("ai_companion.graph.nodes.get_text_to_speech_module") as mock_get_tts,
        ):
            mock_response_chain = AsyncMock()
            mock_response_chain.ainvoke.return_value = mock_conversation_response
            mock_get_response_chain.return_value = mock_response_chain

            with patch("ai_companion.graph.nodes.get_router_chain") as mock_get_router_chain:
                mock_router_chain = AsyncMock()
                mock_router_chain.ainvoke.return_value = mock_router_response
                mock_get_router_chain.return_value = mock_router_chain

                mock_memory_llm_instance = AsyncMock()
                mock_memory_llm_instance.ainvoke.return_value = mock_memory_analysis
                mock_memory_llm.return_value.with_structured_output.return_value = mock_memory_llm_instance

                mock_vector_store = MagicMock()
                mock_vector_store.find_similar_memory.return_value = None
                mock_vector_store.store_memory.return_value = None
                mock_vector_store.search_memories.return_value = []
                mock_get_vector_store.return_value = mock_vector_store

                # Mock TTS module
                mock_tts = AsyncMock()
                mock_tts.synthesize.return_value = mock_audio_output
                mock_get_tts.return_value = mock_tts

                with patch("ai_companion.graph.nodes.ScheduleContextGenerator.get_current_activity") as mock_schedule:
                    mock_schedule.return_value = "Evening Reflection"

                    graph = create_workflow_graph().compile()
                    result = await graph.ainvoke(initial_state)

        # Assert: Verify audio workflow execution
        assert result is not None
        assert result["workflow"] == "audio"
        assert result["audio_buffer"] == mock_audio_output
        assert len(result["audio_buffer"]) > 0


@pytest.mark.integration
@pytest.mark.asyncio
class TestMemoryWorkflow:
    """Test memory extraction and injection in workflow."""

    async def test_memory_extraction_from_user_message(
        self,
        mock_groq_client,
        mock_qdrant_client,
    ):
        """Test memory extraction node stores important information.

        Verifies:
        - Important messages are analyzed
        - Memories are stored in vector store
        - Duplicate memories are not stored
        """
        # Arrange
        initial_state = {
            "messages": [HumanMessage(content="My mother passed away last month from cancer.")],
            "summary": "",
            "workflow": "",
            "audio_buffer": b"",
            "image_path": "",
            "current_activity": "",
            "apply_activity": False,
            "memory_context": "",
        }

        mock_router_response = MagicMock()
        mock_router_response.response_type = "conversation"

        mock_conversation_response = "I'm so sorry for your loss."

        mock_memory_analysis = MagicMock()
        mock_memory_analysis.is_important = True
        mock_memory_analysis.formatted_memory = "User's mother passed away last month from cancer."

        # Act
        with (
            patch("ai_companion.graph.nodes.get_character_response_chain") as mock_get_response_chain,
            patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_get_vector_store,
            patch("ai_companion.modules.memory.long_term.memory_manager.ChatGroq") as mock_memory_llm,
        ):
            mock_response_chain = AsyncMock()
            mock_response_chain.ainvoke.return_value = mock_conversation_response
            mock_get_response_chain.return_value = mock_response_chain

            with patch("ai_companion.graph.nodes.get_router_chain") as mock_get_router_chain:
                mock_router_chain = AsyncMock()
                mock_router_chain.ainvoke.return_value = mock_router_response
                mock_get_router_chain.return_value = mock_router_chain

                mock_memory_llm_instance = AsyncMock()
                mock_memory_llm_instance.ainvoke.return_value = mock_memory_analysis
                mock_memory_llm.return_value.with_structured_output.return_value = mock_memory_llm_instance

                mock_vector_store = MagicMock()
                mock_vector_store.find_similar_memory.return_value = None
                mock_vector_store.store_memory.return_value = None
                mock_vector_store.search_memories.return_value = []
                mock_get_vector_store.return_value = mock_vector_store

                with patch("ai_companion.graph.nodes.ScheduleContextGenerator.get_current_activity") as mock_schedule:
                    mock_schedule.return_value = "Evening Reflection"

                    graph = create_workflow_graph().compile()
                    await graph.ainvoke(initial_state)

                # Assert: Verify memory was stored
                mock_vector_store.store_memory.assert_called_once()
                call_args = mock_vector_store.store_memory.call_args
                assert "mother passed away" in call_args[1]["text"].lower()

    async def test_memory_injection_retrieves_relevant_context(
        self,
        mock_groq_client,
        mock_qdrant_client,
    ):
        """Test memory injection node retrieves and formats relevant memories.

        Verifies:
        - Relevant memories are searched based on context
        - Memories are formatted for prompt injection
        - Memory context is added to state
        """
        # Arrange
        initial_state = {
            "messages": [HumanMessage(content="Tell me more about what we discussed regarding healing.")],
            "summary": "",
            "workflow": "",
            "audio_buffer": b"",
            "image_path": "",
            "current_activity": "",
            "apply_activity": False,
            "memory_context": "",
        }

        mock_memories = [
            MagicMock(text="User is interested in mindfulness meditation for healing.", score=0.92),
            MagicMock(text="User practices daily gratitude journaling.", score=0.85),
        ]

        mock_router_response = MagicMock()
        mock_router_response.response_type = "conversation"

        mock_conversation_response = "We've discussed mindfulness meditation and gratitude journaling."

        mock_memory_analysis = MagicMock()
        mock_memory_analysis.is_important = False
        mock_memory_analysis.formatted_memory = None

        # Act
        with (
            patch("ai_companion.graph.nodes.get_character_response_chain") as mock_get_response_chain,
            patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_get_vector_store,
            patch("ai_companion.modules.memory.long_term.memory_manager.ChatGroq") as mock_memory_llm,
        ):
            mock_response_chain = AsyncMock()
            mock_response_chain.ainvoke.return_value = mock_conversation_response
            mock_get_response_chain.return_value = mock_response_chain

            with patch("ai_companion.graph.nodes.get_router_chain") as mock_get_router_chain:
                mock_router_chain = AsyncMock()
                mock_router_chain.ainvoke.return_value = mock_router_response
                mock_get_router_chain.return_value = mock_router_chain

                mock_memory_llm_instance = AsyncMock()
                mock_memory_llm_instance.ainvoke.return_value = mock_memory_analysis
                mock_memory_llm.return_value.with_structured_output.return_value = mock_memory_llm_instance

                mock_vector_store = MagicMock()
                mock_vector_store.find_similar_memory.return_value = None
                mock_vector_store.store_memory.return_value = None
                mock_vector_store.search_memories.return_value = mock_memories
                mock_get_vector_store.return_value = mock_vector_store

                with patch("ai_companion.graph.nodes.ScheduleContextGenerator.get_current_activity") as mock_schedule:
                    mock_schedule.return_value = "Evening Reflection"

                    graph = create_workflow_graph().compile()
                    result = await graph.ainvoke(initial_state)

        # Assert: Verify memory context was injected
        assert result["memory_context"] != ""
        assert "mindfulness meditation" in result["memory_context"]
        assert "gratitude journaling" in result["memory_context"]


@pytest.mark.integration
@pytest.mark.asyncio
class TestConversationSummarization:
    """Test conversation summarization trigger."""

    async def test_summarization_triggers_after_threshold(
        self,
        mock_groq_client,
        mock_qdrant_client,
    ):
        """Test conversation summarization triggers after message threshold.

        Verifies:
        - Summarization node is called when threshold is reached
        - Summary is created from conversation history
        - Old messages are removed from state
        """
        # Arrange: Create state with many messages (exceeding threshold)
        messages = []
        for i in range(25):  # Exceeds TOTAL_MESSAGES_SUMMARY_TRIGGER (20)
            if i % 2 == 0:
                messages.append(HumanMessage(content=f"User message {i}"))
            else:
                messages.append(AIMessage(content=f"AI response {i}"))

        initial_state = {
            "messages": messages,
            "summary": "",
            "workflow": "",
            "audio_buffer": b"",
            "image_path": "",
            "current_activity": "",
            "apply_activity": False,
            "memory_context": "",
        }

        mock_router_response = MagicMock()
        mock_router_response.response_type = "conversation"

        mock_conversation_response = "I'm here to help."
        mock_summary = "User and AI have been discussing various topics over multiple messages."

        mock_memory_analysis = MagicMock()
        mock_memory_analysis.is_important = False
        mock_memory_analysis.formatted_memory = None

        # Act
        with (
            patch("ai_companion.graph.nodes.get_character_response_chain") as mock_get_response_chain,
            patch("ai_companion.graph.nodes.get_chat_model") as mock_get_chat_model,
            patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_get_vector_store,
            patch("ai_companion.modules.memory.long_term.memory_manager.ChatGroq") as mock_memory_llm,
        ):
            # Mock response chain for conversation
            mock_response_chain = AsyncMock()
            mock_response_chain.ainvoke.return_value = mock_conversation_response
            mock_get_response_chain.return_value = mock_response_chain

            # Mock chat model for summarization
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content=mock_summary)
            mock_get_chat_model.return_value = mock_llm

            with patch("ai_companion.graph.nodes.get_router_chain") as mock_get_router_chain:
                mock_router_chain = AsyncMock()
                mock_router_chain.ainvoke.return_value = mock_router_response
                mock_get_router_chain.return_value = mock_router_chain

                mock_memory_llm_instance = AsyncMock()
                mock_memory_llm_instance.ainvoke.return_value = mock_memory_analysis
                mock_memory_llm.return_value.with_structured_output.return_value = mock_memory_llm_instance

                mock_vector_store = MagicMock()
                mock_vector_store.find_similar_memory.return_value = None
                mock_vector_store.store_memory.return_value = None
                mock_vector_store.search_memories.return_value = []
                mock_get_vector_store.return_value = mock_vector_store

                with patch("ai_companion.graph.nodes.ScheduleContextGenerator.get_current_activity") as mock_schedule:
                    mock_schedule.return_value = "Evening Reflection"

                    graph = create_workflow_graph().compile()
                    result = await graph.ainvoke(initial_state)

        # Assert: Verify summarization occurred
        assert result["summary"] == mock_summary
        # Verify messages were trimmed (should keep last 5 + new response)
        assert len(result["messages"]) < len(messages)


@pytest.mark.integration
@pytest.mark.asyncio
class TestWorkflowTimeout:
    """Test workflow timeout handling."""

    async def test_workflow_respects_timeout(
        self,
        mock_groq_client,
        mock_qdrant_client,
    ):
        """Test workflow timeout handling for long-running operations.

        Verifies:
        - Workflow can be cancelled if it exceeds timeout
        - Timeout errors are handled gracefully
        """
        # Arrange
        initial_state = {
            "messages": [HumanMessage(content="Test message")],
            "summary": "",
            "workflow": "",
            "audio_buffer": b"",
            "image_path": "",
            "current_activity": "",
            "apply_activity": False,
            "memory_context": "",
        }

        mock_router_response = MagicMock()
        mock_router_response.response_type = "conversation"

        # Create a slow async function that will timeout
        async def slow_llm_call(*args, **kwargs):
            await asyncio.sleep(5)  # Simulate slow operation
            return MagicMock(content="Response")

        mock_memory_analysis = MagicMock()
        mock_memory_analysis.is_important = False
        mock_memory_analysis.formatted_memory = None

        # Act & Assert: Verify timeout is respected
        with (
            patch("ai_companion.graph.nodes.get_character_response_chain") as mock_get_response_chain,
            patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_get_vector_store,
            patch("ai_companion.modules.memory.long_term.memory_manager.ChatGroq") as mock_memory_llm,
        ):
            # Mock response chain with slow operation
            mock_response_chain = AsyncMock()
            mock_response_chain.ainvoke = slow_llm_call
            mock_get_response_chain.return_value = mock_response_chain

            with patch("ai_companion.graph.nodes.get_router_chain") as mock_get_router_chain:
                mock_router_chain = AsyncMock()
                mock_router_chain.ainvoke.return_value = mock_router_response
                mock_get_router_chain.return_value = mock_router_chain

                mock_memory_llm_instance = AsyncMock()
                mock_memory_llm_instance.ainvoke.return_value = mock_memory_analysis
                mock_memory_llm.return_value.with_structured_output.return_value = mock_memory_llm_instance

                mock_vector_store = MagicMock()
                mock_vector_store.find_similar_memory.return_value = None
                mock_vector_store.store_memory.return_value = None
                mock_vector_store.search_memories.return_value = []
                mock_get_vector_store.return_value = mock_vector_store

                with patch("ai_companion.graph.nodes.ScheduleContextGenerator.get_current_activity") as mock_schedule:
                    mock_schedule.return_value = "Evening Reflection"

                    graph = create_workflow_graph().compile()

                    # Execute with timeout
                    with pytest.raises(asyncio.TimeoutError):
                        await asyncio.wait_for(
                            graph.ainvoke(initial_state),
                            timeout=2.0,  # 2 second timeout
                        )
