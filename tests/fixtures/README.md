# Test Fixtures

This directory contains reusable test fixtures for the AI Companion test suite.

## Structure

- `conftest.py` - Central fixture configuration that imports and exports all fixtures
- `mock_clients.py` - Mock clients for external services (Groq, ElevenLabs, Qdrant, Together AI)
- `sample_audio.py` - Sample audio file generators for STT testing (WAV, MP3)
- `sample_data.py` - Sample conversation data, messages, and state fixtures

## Usage

All fixtures are automatically available to tests through pytest's fixture discovery mechanism.

### Mock Clients

```python
def test_groq_chat(mock_groq_client):
    """Test using mock Groq client."""
    response = mock_groq_client.chat.completions.create(...)
    assert response.choices[0].message.content
```

### Sample Audio

```python
def test_audio_transcription(sample_wav_file, mock_groq_client):
    """Test STT with sample WAV file."""
    with open(sample_wav_file, 'rb') as audio:
        result = mock_groq_client.audio.transcriptions.create(file=audio)
        assert result.text
```

### Sample Data

```python
def test_conversation_flow(sample_messages, sample_memory_context):
    """Test conversation with sample data."""
    assert len(sample_messages) > 0
    assert sample_memory_context["relevant_memories"]
```

## Available Fixtures

### Mock Clients
- `mock_groq_client` - Mock Groq API client (LLM + STT)
- `mock_elevenlabs_client` - Mock ElevenLabs TTS client
- `mock_tts_client` - Generic TTS client (supports ElevenLabs and future Grok TTS)
- `mock_qdrant_client` - Mock Qdrant vector database client
- `mock_together_client` - Mock Together AI image generation client

### Sample Audio
- `sample_wav_file` - Temporary WAV file (2 seconds, 16kHz)
- `sample_mp3_file` - Temporary MP3 file
- `sample_wav_bytes` - WAV audio as bytes
- `sample_mp3_bytes` - MP3 audio as bytes
- `sample_audio_buffer` - Audio data in BytesIO buffer

### Sample Data
- `sample_user_message` - Single HumanMessage
- `sample_messages` - List of conversation messages
- `sample_memory_context` - Memory context with relevant memories
- `sample_conversation_state` - Complete conversation state for graph testing

## Notes

- Mock clients return realistic test data without making real API calls
- Sample audio files are generated programmatically (no external files needed)
- All fixtures are function-scoped by default (created fresh for each test)
- Async fixtures are supported for async test functions
