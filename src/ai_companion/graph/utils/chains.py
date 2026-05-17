"""Chain construction utilities for LangGraph workflow.

This module provides the character response chain for generating
Rose's therapeutic voice responses.
"""

from typing import Any

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable

from ai_companion.core.prompts import CHARACTER_CARD_PROMPT
from ai_companion.graph.utils.helpers import AsteriskRemovalParser, get_chat_model


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
        system_message += f"\n\nSummary of conversation earlier between Rose and the user: {summary}"

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    return prompt | model | AsteriskRemovalParser()
