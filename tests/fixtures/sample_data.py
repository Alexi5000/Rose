"""Sample data fixtures for testing conversation state and messages."""


import pytest
from langchain_core.messages import AIMessage, HumanMessage


@pytest.fixture
def sample_user_message() -> HumanMessage:
    """Provide a sample user message."""
    return HumanMessage(content="I'm feeling overwhelmed with grief today.")


@pytest.fixture
def sample_messages() -> list[HumanMessage | AIMessage]:
    """Provide a sample conversation with multiple messages."""
    return [
        HumanMessage(content="Hello, I need someone to talk to."),
        AIMessage(content="Hello, dear one. I'm here for you. What's on your heart today?"),
        HumanMessage(content="I lost my mother last month and I'm struggling."),
        AIMessage(
            content="I'm so sorry for your loss. Grief is a sacred journey, and there's no right way to move through it. "
            "Would you like to share more about your mother?"
        ),
    ]


@pytest.fixture
def sample_memory_context() -> dict:
    """Provide sample memory context from long-term memory."""
    return {
        "relevant_memories": [
            {
                "text": "User mentioned losing their mother in a car accident.",
                "timestamp": "2025-10-15T14:30:00",
                "score": 0.92,
            },
            {
                "text": "User finds comfort in nature walks and meditation.",
                "timestamp": "2025-10-18T09:15:00",
                "score": 0.85,
            },
        ],
        "conversation_summary": "User is processing grief after losing their mother. "
        "They have been exploring mindfulness practices.",
    }


@pytest.fixture
def sample_conversation_state() -> dict:
    """Provide a sample conversation state for graph testing."""
    return {
        "messages": [
            HumanMessage(content="Can you help me with a breathing exercise?"),
        ],
        "workflow_type": "conversation",
        "audio_buffer": None,
        "image_path": None,
        "memory_context": {
            "relevant_memories": [],
            "conversation_summary": "",
        },
        "current_activity": {
            "name": "Evening Reflection",
            "time": "20:00",
            "description": "Time for gentle reflection and gratitude practice.",
        },
    }
