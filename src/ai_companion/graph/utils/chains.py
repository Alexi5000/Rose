"""Chain construction utilities for LangGraph workflow.

This module provides functions to create LangChain chains for routing
and character response generation in the Rose AI companion workflow.
"""

from typing import Any

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field

from ai_companion.core.prompts import CHARACTER_CARD_PROMPT, ROUTER_PROMPT
from ai_companion.graph.utils.helpers import AsteriskRemovalParser, get_chat_model


class RouterResponse(BaseModel):
    """Response model for workflow routing decisions.

    Attributes:
        response_type: The workflow type to execute ('conversation' or 'audio')
    """

    response_type: str = Field(
        description="The response type to give to the user. It must be one of: 'conversation' or 'audio'. Default to 'audio' for voice-first healing experience."
    )


def get_router_chain() -> Runnable[dict[str, Any], RouterResponse]:
    """Create a chain for routing user requests to appropriate workflow types.

    This chain analyzes recent messages and determines whether to use
    conversation or audio workflow based on user intent.

    Returns:
        Runnable: Chain that takes messages and returns RouterResponse
    """
    from ai_companion.settings import settings

    model = get_chat_model(temperature=settings.LLM_TEMPERATURE_ROUTER).with_structured_output(RouterResponse)

    prompt = ChatPromptTemplate.from_messages(
        [("system", ROUTER_PROMPT), MessagesPlaceholder(variable_name="messages")]
    )

    return prompt | model


def get_character_response_chain(summary: str = "") -> Runnable[dict[str, Any], str]:
    """Create a chain for generating Rose's character responses.

    This chain uses Rose's character card and conversation context to
    generate empathetic, therapeutic responses.

    Args:
        summary: Optional conversation summary for context continuity

    Returns:
        Runnable: Chain that takes messages and context, returns response text
    """
    model = get_chat_model()
    system_message = CHARACTER_CARD_PROMPT

    if summary:
        system_message += f"\n\nSummary of conversation earlier between Ava and the user: {summary}"

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    return prompt | model | AsteriskRemovalParser()
