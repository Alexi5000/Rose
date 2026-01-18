"""LangGraph workflow nodes for the AI companion.

This module defines all the node functions used in the LangGraph workflow.
Each node represents a discrete processing step in the conversation flow:

- router_node: Determines workflow type (conversation/audio)
- context_injection_node: Injects current activity context
- conversation_node: Generates text responses
- audio_node: Generates voice responses with TTS
- summarize_conversation_node: Summarizes and trims conversation history
- memory_extraction_node: Extracts and stores important information (fire-and-forget)
- memory_injection_node: Retrieves and injects relevant memories

All nodes follow the LangGraph pattern of taking state and optional config,
and returning a dictionary of state updates.

Module Dependencies:
- ai_companion.graph.state: AICompanionState type definition
- ai_companion.graph.utils.chains: LLM chain construction (router, character response)
- ai_companion.graph.utils.helpers: Module factories (chat model, TTS, image generation)
- ai_companion.modules.memory.long_term.memory_manager: Memory operations
- ai_companion.modules.schedules.context_generation: Activity scheduling
- ai_companion.settings: Configuration for message limits, timeouts
- langchain_core.messages: Message types (AIMessage, HumanMessage, RemoveMessage)
- langchain_core.runnables: RunnableConfig for LangGraph
- Standard library: asyncio, os, typing, uuid

Dependents (modules that import this):
- ai_companion.graph.graph: Graph construction and node registration
- Test modules: tests/integration/test_workflow_integration.py

Architecture:
This module is part of the graph layer and orchestrates the conversation workflow
by coordinating between modules (memory, speech, image) and core utilities. Each
node is a pure function that takes state and returns state updates, following
functional programming principles for testability.

For detailed architecture documentation, see:
- docs/ARCHITECTURE.md: LangGraph Workflow Architecture section
- docs/PROJECT_STRUCTURE.md: Graph Architecture section

Example:
    Nodes are typically used within a LangGraph workflow:

    >>> from langgraph.graph import StateGraph
    >>> workflow = StateGraph(AICompanionState)
    >>> workflow.add_node("router", router_node)
    >>> workflow.add_node("conversation", conversation_node)
    >>> # ... add more nodes and edges
"""

import asyncio
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig

from ai_companion.core.logging_config import get_logger
from ai_companion.graph.state import AICompanionState
from ai_companion.graph.utils.chains import (
    get_character_response_chain,
    get_router_chain,
)
from ai_companion.graph.utils.helpers import (
    get_chat_model,
    get_text_to_speech_module,
    node_wrapper,
)
from ai_companion.modules.memory.long_term.memory_manager import get_memory_manager
from ai_companion.modules.schedules.context_generation import ScheduleContextGenerator
from ai_companion.settings import settings

logger = get_logger(__name__)


@node_wrapper
async def router_node(state: AICompanionState) -> dict[str, str]:
    """Route the conversation to the appropriate workflow type.

    Analyzes recent messages to determine if the user wants:
    - conversation: Regular text conversation
    - image: Image generation request
    - audio: Audio/voice interaction

    Args:
        state: Current conversation state

    Returns:
        Dictionary with workflow type: {"workflow": "conversation"|"image"|"audio"}
    """
    chain = get_router_chain()
    response = await chain.ainvoke({"messages": state["messages"][-settings.ROUTER_MESSAGES_TO_ANALYZE :]})
    return {"workflow": response.response_type}


def context_injection_node(state: AICompanionState) -> dict[str, bool | str]:
    """Inject current activity context into the conversation state.

    Determines if the current scheduled activity has changed and should be
    applied to the conversation context.

    Args:
        state: Current conversation state

    Returns:
        Dictionary with activity context: {
            "apply_activity": bool,
            "current_activity": str
        }
    """
    schedule_context = ScheduleContextGenerator.get_current_activity()
    if schedule_context != state.get("current_activity", ""):
        apply_activity = True
    else:
        apply_activity = False
    return {"apply_activity": apply_activity, "current_activity": schedule_context}


@node_wrapper
async def conversation_node(state: AICompanionState, config: RunnableConfig) -> dict[str, AIMessage]:
    """Generate a conversational response using Rose's character.

    Processes the conversation through the character response chain with
    memory context and current activity awareness.

    Args:
        state: Current conversation state
        config: LangGraph runnable configuration

    Returns:
        Dictionary with AI response: {"messages": AIMessage}
    """
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")
    # #region agent log
    import json; _log_path = "/app/src/debug.log"; _log_data = {"location": "nodes.py:conversation_node", "message": "LLM input context", "hypothesisId": "A,C,D", "data": {"message_count": len(state.get("messages", [])), "messages_last_3": [{"type": m.type, "content": m.content[:100] if hasattr(m, "content") else str(m)[:100]} for m in state.get("messages", [])[-3:]], "memory_context_len": len(memory_context), "memory_context_preview": memory_context[:300] if memory_context else "(empty)", "session_id": config.get("configurable", {}).get("thread_id") if config else None, "summary": state.get("summary", "")[:200] if state.get("summary") else "(no summary)"}, "timestamp": __import__("datetime").datetime.now().isoformat()}; open(_log_path, "a").write(json.dumps(_log_data) + "\n")
    # #endregion

    chain = get_character_response_chain(state.get("summary", ""))

    try:
        response = await chain.ainvoke(
            {
                "messages": state["messages"],
                "current_activity": current_activity,
                "memory_context": memory_context,
            },
            config,
        )
    except Exception as e:
        # Return a gentle fallback message instead of failing the entire workflow
        logger.exception("❌ conversation chain invocation failed; returning fallback message")
        fallback_text = "I'm having trouble processing that right now. Could you try asking in a different way?"
        return {"messages": AIMessage(content=fallback_text)}

    # #region agent log
    import json; _log_path = "/app/src/debug.log"; _log_data = {"location": "nodes.py:conversation_node:response", "message": "LLM response", "hypothesisId": "D", "data": {"response_length": len(response), "response_preview": response[:300] if response else "(empty)"}, "timestamp": __import__("datetime").datetime.now().isoformat()}; open(_log_path, "a").write(json.dumps(_log_data) + "\n")
    # #endregion
    return {"messages": AIMessage(content=response)}


@node_wrapper
async def audio_node(state: AICompanionState, config: RunnableConfig) -> dict[str, str | bytes]:
    """Generate a voice response with audio output.

    Creates a text response and synthesizes it to audio using TTS.

    Args:
        state: Current conversation state
        config: LangGraph runnable configuration

    Returns:
        Dictionary with response and audio: {
            "messages": str,
            "audio_buffer": bytes
        }
    """
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")
    # #region agent log
    import json; _log_path = "/app/src/debug.log"; _log_data = {"location": "nodes.py:audio_node:input", "message": "Audio node LLM input", "hypothesisId": "A,C,D", "data": {"message_count": len(state.get("messages", [])), "messages_content": [{"type": m.type, "content": m.content if hasattr(m, "content") else str(m)} for m in state.get("messages", [])], "memory_context": memory_context if memory_context else "(empty)", "current_activity": current_activity, "session_id": config.get("configurable", {}).get("thread_id") if config else None, "summary": state.get("summary", "") if state.get("summary") else "(no summary)"}, "timestamp": __import__("datetime").datetime.now().isoformat()}; open(_log_path, "a").write(json.dumps(_log_data) + "\n")
    # #endregion

    chain = get_character_response_chain(state.get("summary", ""))
    text_to_speech_module = get_text_to_speech_module()

    try:
        response = await chain.ainvoke(
        {
            "messages": state["messages"],
            "current_activity": current_activity,
            "memory_context": memory_context,
        },
        config,
    )
        # #region agent log
        import json; _log_path = "/app/src/debug.log"; _log_data = {"location": "nodes.py:audio_node:llm_response", "message": "Audio node LLM response", "hypothesisId": "D", "data": {"response_text": response, "response_len": len(response) if response else 0}, "timestamp": __import__("datetime").datetime.now().isoformat()}; open(_log_path, "a").write(json.dumps(_log_data) + "\n")
        # #endregion
    except Exception as e:
        logger.exception("❌ conversation chain invocation failed in audio_node")
        raise

    # Use safe TTS with fallback to avoid failing the whole workflow
    try:
        audio_bytes, text_fallback = await text_to_speech_module.synthesize_with_fallback(response)
    except Exception:
        logger.exception("❌ TTS synth failed in audio_node; falling back to text-only")
        audio_bytes = None
        text_fallback = response

    return {"messages": AIMessage(content=text_fallback), "audio_buffer": audio_bytes}


@node_wrapper
async def summarize_conversation_node(state: AICompanionState) -> dict[str, str | list[RemoveMessage]]:
    """Summarize conversation history and trim old messages.

    Creates or extends a conversation summary and removes old messages
    to keep the context window manageable.

    Args:
        state: Current conversation state

    Returns:
        Dictionary with summary and messages to remove: {
            "summary": str,
            "messages": list[RemoveMessage]
        }
    """
    model = get_chat_model()
    summary = state.get("summary", "")

    if summary:
        summary_message = (
            f"This is summary of the conversation to date between Rose and the user: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )
    else:
        summary_message = (
            "Create a summary of the conversation above between Rose and the user. "
            "The summary must be a short description of the conversation so far, "
            "but that captures all the relevant information shared between Rose and the user:"
        )

    messages = state["messages"] + [HumanMessage(content=summary_message)]
    try:
        response = await model.ainvoke(messages)
    except Exception:
        logger.exception("❌ summarize_conversation_node model invocation failed; keeping current summary unchanged")
        # Preserve the existing summary and avoid deleting current messages
        return {"summary": summary, "messages": []}

    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][: -settings.TOTAL_MESSAGES_AFTER_SUMMARY]]
    return {"summary": response.content, "messages": delete_messages}


async def _extract_memories_background(message: Any, session_id: str | None) -> None:
    """Background task for memory extraction.
    
    This runs as a fire-and-forget task to avoid blocking the main workflow.
    Any exceptions are caught and logged but do not propagate.
    
    Args:
        message: The message to extract memories from
        session_id: Session identifier for memory isolation
    """
    try:
        memory_manager = get_memory_manager()
        await memory_manager.extract_and_store_memories(message, session_id=session_id)
        logger.debug("background_memory_extraction_complete", session_id=session_id)
    except Exception as e:
        # Background task failures are logged but never propagate
        logger.warning(f"⚠️ Background memory extraction failed: {e}", exc_info=True)


@node_wrapper
async def memory_extraction_node(state: AICompanionState, config: RunnableConfig) -> dict[str, Any]:
    """Extract and store important information from the last message (non-blocking).

    Phase 1 Optimization: Memory extraction is now fire-and-forget.
    This node spawns a background task and returns immediately,
    reducing the critical path latency by ~100-200ms.

    The background task:
    - Analyzes the most recent message for important information
    - Stores relevant memories in Qdrant (long-term memory)
    - Logs any failures but never breaks the main workflow

    Args:
        state: Current conversation state
        config: LangGraph runnable configuration (contains session_id)

    Returns:
        Empty dictionary (proceeds immediately without waiting for extraction)
    """
    if not state["messages"]:
        return {}

    try:
        # Extract session_id from config for memory isolation
        session_id = config.get("configurable", {}).get("thread_id") if config else None
        message = state["messages"][-1]

        # Fire-and-forget: spawn background task and return immediately
        # This reduces critical path latency while still storing memories
        asyncio.create_task(
            _extract_memories_background(message, session_id),
            name=f"memory_extraction_{session_id or 'unknown'}"
        )
        logger.debug("memory_extraction_task_spawned", session_id=session_id)
    except Exception as e:
        # Even task creation failure should not break the workflow
        logger.warning(f"⚠️ Failed to spawn memory extraction task: {e}", exc_info=True)
    
    return {}


@node_wrapper
def memory_injection_node(state: AICompanionState, config: RunnableConfig) -> dict[str, str]:
    """Retrieve and inject relevant memories into the character card.

    Searches long-term memory for relevant context based on recent
    conversation and formats it for inclusion in the prompt.

    Args:
        state: Current conversation state
        config: LangGraph runnable configuration (contains session_id)

    Returns:
        Dictionary with memory context: {"memory_context": str}
    """
    memory_manager = get_memory_manager()

    # Extract session_id from config for memory isolation
    session_id = config.get("configurable", {}).get("thread_id") if config else None

    # Get relevant memories based on recent conversation
    recent_context = " ".join([m.content for m in state["messages"][-3:]])
    # #region agent log
    import json; _log_path = "/app/src/debug.log"; _log_data = {"location": "nodes.py:memory_injection_node:query", "message": "Memory query context", "hypothesisId": "B,E", "data": {"session_id": session_id, "recent_context_len": len(recent_context), "recent_context_preview": recent_context[:300] if recent_context else "(empty)"}, "timestamp": __import__("datetime").datetime.now().isoformat()}; open(_log_path, "a").write(json.dumps(_log_data) + "\n")
    # #endregion
    try:
        memories = memory_manager.get_relevant_memories(recent_context, session_id=session_id)
    except Exception as e:
        logger.warning(f"⚠️ Long-term memory retrieval failed: {e}", exc_info=True)
        memories = []

    # Format memories for the character card
    memory_context = memory_manager.format_memories_for_prompt(memories)
    # #region agent log
    import json; _log_path = "/app/src/debug.log"; _log_data = {"location": "nodes.py:memory_injection_node:result", "message": "Memory injection result", "hypothesisId": "B", "data": {"memories_count": len(memories), "memories_preview": memories[:3] if memories else [], "formatted_context_len": len(memory_context)}, "timestamp": __import__("datetime").datetime.now().isoformat()}; open(_log_path, "a").write(json.dumps(_log_data) + "\n")
    # #endregion

    return {"memory_context": memory_context}
