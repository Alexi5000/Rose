"""Mock API response fixtures for testing.

This module provides sample API responses from external services
to enable consistent testing without actual API calls.
"""

from datetime import datetime
from typing import Any, Dict, List

import pytest


@pytest.fixture
def mock_groq_transcription_response() -> Dict[str, Any]:
    """Mock Groq STT transcription response.

    Returns:
        dict: Sample transcription response matching Groq API format
    """
    return {
        "text": "Hello, I'm feeling anxious today and need someone to talk to.",
        "language": "en",
        "duration": 5.2,
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 5.2,
                "text": "Hello, I'm feeling anxious today and need someone to talk to.",
                "tokens": [1, 2, 3, 4, 5],
                "temperature": 0.0,
                "avg_logprob": -0.3,
                "compression_ratio": 1.5,
                "no_speech_prob": 0.01,
            }
        ],
    }


@pytest.fixture
def mock_groq_chat_response() -> Dict[str, Any]:
    """Mock Groq chat completion response.

    Returns:
        dict: Sample chat completion response matching Groq API format
    """
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": "llama-3.3-70b-versatile",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "I hear you, and I'm here for you. Anxiety can feel overwhelming, but you're not alone. Let's take this one step at a time together.",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 150, "completion_tokens": 35, "total_tokens": 185},
    }


@pytest.fixture
def mock_elevenlabs_audio_response() -> bytes:
    """Mock ElevenLabs TTS audio response.

    Note: ElevenLabs is configured but may not be actively used.

    Returns:
        bytes: Sample MP3 audio data
    """
    # Minimal MP3 header + some data
    mp3_header = bytes([0xFF, 0xFB, 0x90, 0x00])
    return mp3_header + (b"\x00" * 2048)


@pytest.fixture
def mock_qdrant_search_response() -> List[Dict[str, Any]]:
    """Mock Qdrant vector search response.

    Returns:
        list: Sample search results matching Qdrant API format
    """
    return [
        {
            "id": "memory_001",
            "score": 0.95,
            "payload": {
                "text": "User mentioned feeling anxious about work deadlines",
                "timestamp": "2024-01-15T10:30:00Z",
                "metadata": {"emotion": "anxiety", "topic": "work"},
            },
            "vector": None,  # Vector not returned in search results
        },
        {
            "id": "memory_002",
            "score": 0.87,
            "payload": {
                "text": "User finds deep breathing exercises helpful for anxiety",
                "timestamp": "2024-01-14T15:20:00Z",
                "metadata": {"emotion": "calm", "topic": "coping_strategies"},
            },
            "vector": None,
        },
        {
            "id": "memory_003",
            "score": 0.82,
            "payload": {
                "text": "User has been working on mindfulness practices",
                "timestamp": "2024-01-13T09:15:00Z",
                "metadata": {"topic": "mindfulness"},
            },
            "vector": None,
        },
    ]


@pytest.fixture
def mock_qdrant_upsert_response() -> Dict[str, Any]:
    """Mock Qdrant upsert operation response.

    Returns:
        dict: Sample upsert response matching Qdrant API format
    """
    return {"operation_id": 12345, "status": "completed"}


@pytest.fixture
def mock_memory_extraction_result() -> Dict[str, Any]:
    """Mock memory extraction result from LLM.

    Returns:
        dict: Sample extracted memory with metadata
    """
    return {
        "memory": "User is experiencing anxiety about work deadlines and finds it overwhelming",
        "emotion": "anxiety",
        "topics": ["work", "stress", "deadlines"],
        "importance": "high",
        "timestamp": datetime.now().isoformat(),
    }


@pytest.fixture
def mock_router_decision() -> Dict[str, str]:
    """Mock router decision for workflow routing.

    Returns:
        dict: Sample router decision
    """
    return {"workflow_type": "conversation", "reasoning": "User is seeking emotional support through conversation"}


@pytest.fixture
def mock_langgraph_state() -> Dict[str, Any]:
    """Mock LangGraph workflow state.

    Returns:
        dict: Sample workflow state matching AICompanionState schema
    """
    return {
        "messages": [{"role": "user", "content": "I'm feeling anxious today"}],
        "workflow_type": "conversation",
        "audio_buffer": None,
        "image_path": None,
        "memory_context": [],
        "current_activity": None,
        "metadata": {},
    }
