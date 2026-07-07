"""LangGraph workflow nodes for the Rose AI companion.

This module defines all the node functions used in the voice-first LangGraph workflow.
Each node represents a discrete processing step in the conversation flow:

- context_injection_node: Injects current activity context
- conversation_node: Generates text responses (used for testing)
- audio_node: Generates voice responses with TTS
- summarize_conversation_node: Summarizes and trims conversation history
- memory_extraction_node: Extracts and stores important information (fire-and-forget)
- memory_injection_node: Retrieves and injects relevant memories

All nodes follow the LangGraph pattern of taking state and optional config,
and returning a dictionary of state updates.

Example:
    Nodes are registered in the workflow graph:

    >>> from langgraph.graph import StateGraph
    >>> workflow = StateGraph(AICompanionState)
    >>> workflow.add_node("audio_node", audio_node)
    >>> workflow.add_node("memory_extraction_node", memory_extraction_node)
"""

import asyncio
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig

from ai_companion.core.logging_config import get_logger
from ai_companion.core.metrics import metrics
from ai_companion.core.privacy_logging import exc_info_for_log, exception_message_for_log, session_id_for_log
from ai_companion.core.prompts import get_session_arc_hint
from ai_companion.graph.state import AICompanionState
from ai_companion.graph.utils.chains import get_character_response_chain
from ai_companion.graph.utils.helpers import (
    get_memory_module,
    get_safety_classifier_module,
    get_text_to_speech_module,
    node_wrapper,
)
from ai_companion.modules.affect import classify_affect_state
from ai_companion.modules.memory.privacy import is_long_term_memory_enabled
from ai_companion.modules.providers import get_chat_model
from ai_companion.modules.response_quality import analyze_voice_response, sanitize_voice_response
from ai_companion.modules.schedules.context_generation import ScheduleContextGenerator
from ai_companion.settings import settings

logger = get_logger(__name__)


def _record_voice_response_quality(response: str) -> None:
    """Record deterministic voice-quality issues without logging response text."""

    issues = analyze_voice_response(response)
    if not issues:
        return

    issue_codes = [issue.code for issue in issues]
    for issue_code in issue_codes:
        metrics.increment_counter("voice_response_quality_issues_total", tags={"issue_code": issue_code})

    logger.warning(
        "voice_response_quality_issues",
        issue_codes=issue_codes,
        issue_count=len(issue_codes),
        response_words=len(response.split()),
    )


def safety_node(state: AICompanionState) -> dict[str, str]:
    """Assess user input before normal generation."""
    if not state["messages"]:
        return {"safety_risk": "", "safety_response": ""}

    latest_message = state["messages"][-1]
    latest_text = str(getattr(latest_message, "content", ""))
    safety_classifier = get_safety_classifier_module()
    assessment = safety_classifier.assess(latest_text)

    if not assessment.is_crisis:
        return {"safety_risk": "", "safety_response": ""}

    risk = "imminent_crisis" if assessment.is_imminent else "crisis"
    logger.warning("crisis_risk_detected", safety_risk=risk)
    return {"safety_risk": risk, "safety_response": assessment.response or ""}


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


def affect_tracking_node(state: AICompanionState) -> dict[str, str]:
    """Classify the latest user turn into a non-clinical affect hint."""

    if not state["messages"]:
        return {"affect_state": ""}

    latest_message = state["messages"][-1]
    latest_text = str(getattr(latest_message, "content", ""))
    affect_state = classify_affect_state(latest_text).format_for_prompt()
    return {"affect_state": affect_state}


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
    affect_state = state.get("affect_state", "")
    session_arc = get_session_arc_hint(len(state["messages"]), affect_state)

    chain = get_character_response_chain(state.get("summary", ""))

    try:
        response = await chain.ainvoke(
            {
                "messages": state["messages"],
                "current_activity": current_activity,
                "memory_context": memory_context,
                "affect_state": affect_state,
                "session_arc": session_arc,
            },
            config,
        )
    except Exception as e:
        # Return a gentle fallback message instead of failing the entire workflow
        logger.error(
            "conversation_chain_invocation_failed_fallback",
            error=exception_message_for_log(e),
            error_type=type(e).__name__,
            exc_info=exc_info_for_log(),
        )
        fallback_text = "I'm having trouble processing that right now. Could you try asking in a different way?"
        return {"messages": AIMessage(content=fallback_text)}

    response = sanitize_voice_response(response)
    _record_voice_response_quality(response)
    return {"messages": AIMessage(content=response)}


@node_wrapper
async def audio_node(state: AICompanionState, config: RunnableConfig) -> dict[str, str | bytes | None]:
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
    affect_state = state.get("affect_state", "")
    session_arc = get_session_arc_hint(len(state["messages"]), affect_state)
    configurable = config.get("configurable", {}) if config else {}
    skip_tts = bool(configurable.get("skip_tts"))

    safety_response = state.get("safety_response", "")
    if safety_response:
        response = safety_response
    else:
        chain = get_character_response_chain(state.get("summary", ""))
        try:
            response = await chain.ainvoke(
                {
                    "messages": state["messages"],
                    "current_activity": current_activity,
                    "memory_context": memory_context,
                    "affect_state": affect_state,
                    "session_arc": session_arc,
                },
                config,
            )
        except Exception as e:
            logger.error(
                "conversation_chain_invocation_failed_in_audio_node",
                error=exception_message_for_log(e),
                error_type=type(e).__name__,
                exc_info=exc_info_for_log(),
            )
            raise

    response = sanitize_voice_response(response)

    if skip_tts:
        logger.debug("audio_node_skip_tts", reason="configurable.skip_tts")
        _record_voice_response_quality(response)
        return {"messages": AIMessage(content=response), "audio_buffer": None}

    _record_voice_response_quality(response)

    # Use safe TTS with fallback to avoid failing the whole workflow.
    # Always store the original `response` as the AI message content - never the
    # TTS fallback error string ("I'm having trouble with my voice...") which
    # would corrupt the conversation state and be re-sent to TTS on retry.
    text_to_speech_module = get_text_to_speech_module()
    try:
        audio_bytes, _ = await text_to_speech_module.synthesize_with_fallback(response)
    except Exception as e:
        logger.error(
            "tts_synthesis_failed_in_audio_node_fallback",
            error=exception_message_for_log(e),
            error_type=type(e).__name__,
            exc_info=exc_info_for_log(),
        )
        audio_bytes = None

    return {"messages": AIMessage(content=response), "audio_buffer": audio_bytes}


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
    except Exception as e:
        logger.error(
            "summarize_conversation_model_invocation_failed",
            error=exception_message_for_log(e),
            error_type=type(e).__name__,
            exc_info=exc_info_for_log(),
        )
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
        memory = get_memory_module()
        await memory.extract_and_store_memories(message, session_id=session_id)
        logger.debug("background_memory_extraction_complete", session_log_id=session_id_for_log(session_id))
    except Exception as e:
        # Background task failures are logged but never propagate
        logger.warning(
            "background_memory_extraction_failed",
            error=exception_message_for_log(e),
            exc_info=exc_info_for_log(),
        )


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
        if not is_long_term_memory_enabled(session_id):
            logger.debug("memory_extraction_skipped_session_only", session_log_id=session_id_for_log(session_id))
            return {}

        message = state["messages"][-1]

        # Fire-and-forget: spawn background task and return immediately
        # This reduces critical path latency while still storing memories
        asyncio.create_task(
            _extract_memories_background(message, session_id),
            name=f"memory_extraction_{session_id_for_log(session_id)}",
        )
        logger.debug("memory_extraction_task_spawned", session_log_id=session_id_for_log(session_id))
    except Exception as e:
        # Even task creation failure should not break the workflow
        logger.warning(
            "memory_extraction_task_spawn_failed",
            error=exception_message_for_log(e),
            exc_info=exc_info_for_log(),
        )

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
    # Extract session_id from config for memory isolation
    session_id = config.get("configurable", {}).get("thread_id") if config else None
    if not is_long_term_memory_enabled(session_id):
        logger.debug("memory_injection_skipped_session_only", session_log_id=session_id_for_log(session_id))
        return {"memory_context": ""}

    memory = get_memory_module()

    # Get relevant memories based on recent conversation
    recent_context = " ".join([m.content for m in state["messages"][-3:]])
    try:
        if hasattr(memory, "get_relevant_memory_records") and hasattr(memory, "format_memory_records_for_prompt"):
            memory_records = memory.get_relevant_memory_records(recent_context, session_id=session_id)
            memory_context = memory.format_memory_records_for_prompt(memory_records)
        else:
            memories = memory.get_relevant_memories(recent_context, session_id=session_id)
            memory_context = memory.format_memories_for_prompt(memories)
    except Exception as e:
        logger.warning(
            "long_term_memory_retrieval_failed",
            error=exception_message_for_log(e),
            exc_info=exc_info_for_log(),
        )
        memory_context = ""

    return {"memory_context": memory_context}
