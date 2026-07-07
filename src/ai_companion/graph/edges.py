from langgraph.graph import END
from typing_extensions import Literal

from ai_companion.graph.state import AICompanionState
from ai_companion.settings import settings


def should_use_crisis_response(
    state: AICompanionState,
) -> Literal["audio_node", "affect_tracking_node"]:
    if state.get("safety_risk") in {"crisis", "imminent_crisis"}:
        return "audio_node"

    return "affect_tracking_node"


def should_summarize_conversation(
    state: AICompanionState,
) -> Literal["summarize_conversation_node", "__end__"]:
    messages = state["messages"]

    if len(messages) > settings.TOTAL_MESSAGES_SUMMARY_TRIGGER:
        return "summarize_conversation_node"

    return END
