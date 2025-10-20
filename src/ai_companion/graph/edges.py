from langgraph.graph import END
from typing_extensions import Literal

from ai_companion.graph.state import AICompanionState
from ai_companion.settings import settings


def should_summarize_conversation(
    state: AICompanionState,
) -> Literal["summarize_conversation_node", "__end__"]:
    messages = state["messages"]

    if len(messages) > settings.TOTAL_MESSAGES_SUMMARY_TRIGGER:
        return "summarize_conversation_node"

    return END


def select_workflow(
    state: AICompanionState,
) -> Literal["conversation_node", "audio_node"]:
    """Route to conversation or audio node only. Image workflow disabled for Rose."""
    workflow = state["workflow"]

    if workflow == "audio":
        return "audio_node"
    else:
        # Default to conversation for any other workflow type
        return "conversation_node"
