"""Validation tests for test fixtures and infrastructure."""

import pytest


@pytest.mark.unit
def test_mock_groq_client(mock_groq_client):
    """Verify mock Groq client fixture works correctly."""
    # Test chat completion
    response = mock_groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": "Hello"}]
    )
    assert response.choices[0].message.content
    assert "test response" in response.choices[0].message.content.lower()

    # Test audio transcription
    transcription = mock_groq_client.audio.transcriptions.create(
        file=("test.wav", b"fake_audio_data"), model="whisper-large-v3"
    )
    assert transcription.text
    assert "test transcription" in transcription.text.lower()


@pytest.mark.unit
def test_mock_tts_client(mock_tts_client):
    """Verify mock TTS client fixture works correctly."""
    # Test generate method (iterator)
    audio_chunks = list(mock_tts_client.generate(text="Hello world"))
    assert len(audio_chunks) > 0
    assert all(isinstance(chunk, bytes) for chunk in audio_chunks)

    # Test synthesize method (direct bytes)
    audio_data = mock_tts_client.synthesize(text="Hello world")
    assert isinstance(audio_data, bytes)
    assert len(audio_data) > 0


@pytest.mark.unit
def test_mock_qdrant_client(mock_qdrant_client):
    """Verify mock Qdrant client fixture works correctly."""
    # Test collection exists
    exists = mock_qdrant_client.collection_exists("test_collection")
    assert exists is True

    # Test search
    results = mock_qdrant_client.search(collection_name="test_collection", query_vector=[0.1] * 384, limit=5)
    assert len(results) > 0
    assert results[0].score > 0
    assert "payload" in dir(results[0])


@pytest.mark.unit
def test_sample_wav_file(sample_wav_file):
    """Verify sample WAV file fixture creates valid file."""
    assert sample_wav_file.exists()
    assert sample_wav_file.suffix == ".wav"
    assert sample_wav_file.stat().st_size > 0


@pytest.mark.unit
def test_sample_wav_bytes(sample_wav_bytes):
    """Verify sample WAV bytes fixture provides valid data."""
    assert isinstance(sample_wav_bytes, bytes)
    assert len(sample_wav_bytes) > 44  # WAV header is 44 bytes
    # Check for WAV header signature
    assert sample_wav_bytes[:4] == b"RIFF"
    assert sample_wav_bytes[8:12] == b"WAVE"


@pytest.mark.unit
def test_sample_audio_buffer(sample_audio_buffer):
    """Verify sample audio buffer fixture works correctly."""
    assert sample_audio_buffer.tell() == 0  # Buffer at start
    data = sample_audio_buffer.read()
    assert len(data) > 0
    assert isinstance(data, bytes)


@pytest.mark.unit
def test_sample_user_message(sample_user_message):
    """Verify sample user message fixture."""
    assert sample_user_message.content
    assert isinstance(sample_user_message.content, str)
    assert len(sample_user_message.content) > 0


@pytest.mark.unit
def test_sample_messages(sample_messages):
    """Verify sample messages fixture."""
    assert len(sample_messages) > 0
    assert all(hasattr(msg, "content") for msg in sample_messages)


@pytest.mark.unit
def test_sample_memory_context(sample_memory_context):
    """Verify sample memory context fixture."""
    assert "relevant_memories" in sample_memory_context
    assert "conversation_summary" in sample_memory_context
    assert isinstance(sample_memory_context["relevant_memories"], list)


@pytest.mark.unit
def test_sample_conversation_state(sample_conversation_state):
    """Verify sample conversation state fixture."""
    assert "messages" in sample_conversation_state
    assert "workflow_type" in sample_conversation_state
    assert sample_conversation_state["workflow_type"] == "conversation"
