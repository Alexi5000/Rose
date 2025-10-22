"""Mock client fixtures for external services."""

from typing import Iterator
from unittest.mock import MagicMock

import pytest
from groq import Groq
from qdrant_client import QdrantClient


@pytest.fixture
def mock_groq_client() -> Iterator[MagicMock]:
    """Mock Groq client for LLM and STT testing."""
    mock_client = MagicMock(spec=Groq)

    # Mock chat completions
    mock_chat = MagicMock()
    mock_chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content="This is a test response from the AI companion.",
                    role="assistant"
                )
            )
        ]
    )
    mock_client.chat = mock_chat

    # Mock audio transcriptions (STT)
    mock_audio = MagicMock()
    mock_audio.transcriptions.create.return_value = MagicMock(
        text="This is a test transcription from audio."
    )
    mock_client.audio = mock_audio

    yield mock_client


@pytest.fixture
def mock_elevenlabs_client() -> Iterator[MagicMock]:
    """Mock ElevenLabs client for TTS testing."""
    mock_client = MagicMock()

    # Mock text-to-speech generation
    mock_client.generate.return_value = iter([b"fake_audio_chunk_1", b"fake_audio_chunk_2"])

    yield mock_client


@pytest.fixture
def mock_tts_client() -> Iterator[MagicMock]:
    """Generic mock TTS client (supports both ElevenLabs and future Grok TTS)."""
    mock_client = MagicMock()

    # Mock text-to-speech generation with generic interface
    mock_client.generate.return_value = iter([b"fake_audio_chunk_1", b"fake_audio_chunk_2"])
    mock_client.synthesize.return_value = b"fake_audio_data"

    yield mock_client


@pytest.fixture
def mock_qdrant_client() -> Iterator[MagicMock]:
    """Mock Qdrant client for vector database testing."""
    mock_client = MagicMock(spec=QdrantClient)

    # Mock collection operations
    mock_client.collection_exists.return_value = True
    mock_client.create_collection.return_value = None

    # Mock search operations
    mock_client.search.return_value = [
        MagicMock(
            id="test_id_1",
            score=0.95,
            payload={
                "text": "Previous conversation about grief and healing.",
                "timestamp": "2025-10-20T10:00:00",
                "conversation_id": "test_conv_1"
            }
        ),
        MagicMock(
            id="test_id_2",
            score=0.87,
            payload={
                "text": "Discussion about mindfulness practices.",
                "timestamp": "2025-10-19T15:30:00",
                "conversation_id": "test_conv_2"
            }
        )
    ]

    # Mock upsert operations
    mock_client.upsert.return_value = None

    # Mock delete operations
    mock_client.delete.return_value = None

    yield mock_client


@pytest.fixture
def mock_together_client() -> Iterator[MagicMock]:
    """Mock Together AI client for image generation testing."""
    mock_client = MagicMock()

    # Mock image generation
    mock_response = MagicMock()
    mock_response.data = [
        MagicMock(
            b64_json="fake_base64_encoded_image_data",
            url="https://example.com/generated_image.png"
        )
    ]
    mock_client.images.generate.return_value = mock_response

    yield mock_client
