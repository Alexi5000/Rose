"""Pytest configuration and shared fixtures."""


# Import all fixtures to make them available to tests
from tests.fixtures.mock_clients import (
    mock_elevenlabs_client,
    mock_groq_client,
    mock_qdrant_client,
    mock_together_client,
    mock_tts_client,
)
from tests.fixtures.sample_audio import (
    sample_audio_buffer,
    sample_mp3_bytes,
    sample_mp3_file,
    sample_wav_bytes,
    sample_wav_file,
)
from tests.fixtures.sample_data import (
    sample_conversation_state,
    sample_memory_context,
    sample_messages,
    sample_user_message,
)

# Re-export fixtures
__all__ = [
    # Mock clients
    "mock_groq_client",
    "mock_elevenlabs_client",
    "mock_tts_client",
    "mock_qdrant_client",
    "mock_together_client",
    # Sample audio
    "sample_wav_file",
    "sample_mp3_file",
    "sample_wav_bytes",
    "sample_mp3_bytes",
    "sample_audio_buffer",
    # Sample data
    "sample_user_message",
    "sample_messages",
    "sample_memory_context",
    "sample_conversation_state",
]
