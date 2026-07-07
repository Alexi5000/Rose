"""LangGraph workflow graph construction.

This module defines the voice-first conversation workflow graph for Rose,
orchestrating memory extraction, context injection, and audio response generation.
"""

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from ai_companion.graph.edges import (
    should_summarize_conversation,
    should_use_crisis_response,
)
from ai_companion.graph.nodes import (
    affect_tracking_node,
    audio_node,
    context_injection_node,
    memory_extraction_node,
    memory_injection_node,
    safety_node,
    summarize_conversation_node,
)
from ai_companion.graph.state import AICompanionState


@lru_cache(maxsize=1)
def create_workflow_graph() -> StateGraph:
    graph_builder = StateGraph(AICompanionState)

    # Voice-first workflow: router node removed to eliminate one LLM call
    # (~500-1000ms latency savings per turn). All voice interactions go
    # directly to audio_node.
    graph_builder.add_node("safety_node", safety_node)
    graph_builder.add_node("affect_tracking_node", affect_tracking_node)
    graph_builder.add_node("memory_extraction_node", memory_extraction_node)
    graph_builder.add_node("context_injection_node", context_injection_node)
    graph_builder.add_node("memory_injection_node", memory_injection_node)
    graph_builder.add_node("audio_node", audio_node)
    graph_builder.add_node("summarize_conversation_node", summarize_conversation_node)

    # Flow: safety check -> affect hint -> extract memories -> inject context -> inject memories -> generate audio response
    # Crisis responses bypass normal LLM generation and memory injection.
    graph_builder.add_edge(START, "safety_node")
    graph_builder.add_conditional_edges("safety_node", should_use_crisis_response)
    graph_builder.add_edge("affect_tracking_node", "memory_extraction_node")
    graph_builder.add_edge("memory_extraction_node", "context_injection_node")
    graph_builder.add_edge("context_injection_node", "memory_injection_node")
    graph_builder.add_edge("memory_injection_node", "audio_node")

    # Summarize if conversation history exceeds threshold
    graph_builder.add_conditional_edges("audio_node", should_summarize_conversation)
    graph_builder.add_edge("summarize_conversation_node", END)

    return graph_builder


# Compiled without a checkpointer. Used for LangGraph Studio
graph = create_workflow_graph().compile()
