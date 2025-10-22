# Test Infrastructure Setup

This document describes the test infrastructure for the AI Companion application.

## Directory Structure

```
tests/
├── fixtures/              # Reusable test fixtures
│   ├── conftest.py       # Fixture exports
│   ├── mock_clients.py   # Mock external service clients
│   ├── sample_audio.py   # Audio file generators
│   ├── sample_data.py    # Sample conversation data
│   └── README.md         # Fixture documentation
├── unit/                 # Unit tests
│   ├── test_fixtures_validation.py
│   └── README.md
├── integration/          # Integration tests
│   └── README.md
├── conftest.py          # Root pytest configuration
└── pytest.ini           # Pytest settings
```

## Test Dependencies

All test dependencies are installed via `pyproject.toml`:

- `pytest==8.4.2` - Test framework
- `pytest-asyncio==1.2.0` - Async test support
- `pytest-mock==3.15.1` - Mocking utilities
- `pytest-cov==7.0.0` - Coverage reporting

## Running Tests

### All Tests
```bash
pytest tests/
```

### Unit Tests Only
```bash
pytest tests/unit -m unit
```

### Integration Tests Only
```bash
pytest tests/integration -m integration
```

### With Coverage
```bash
pytest tests/ --cov=src/ai_companion --cov-report=html
```

### Specific Test File
```bash
pytest tests/unit/test_fixtures_validation.py -v
```

## Available Fixtures

### Mock Clients
- `mock_groq_client` - Groq API (LLM + STT)
- `mock_elevenlabs_client` - ElevenLabs TTS
- `mock_tts_client` - Generic TTS (supports ElevenLabs and future Grok TTS)
- `mock_qdrant_client` - Qdrant vector database
- `mock_together_client` - Together AI image generation

### Sample Audio
- `sample_wav_file` - Temporary WAV file (2s, 16kHz)
- `sample_mp3_file` - Temporary MP3 file
- `sample_wav_bytes` - WAV audio as bytes
- `sample_mp3_bytes` - MP3 audio as bytes
- `sample_audio_buffer` - Audio in BytesIO buffer

### Sample Data
- `sample_user_message` - Single HumanMessage
- `sample_messages` - Conversation message list
- `sample_memory_context` - Memory context with relevant memories
- `sample_conversation_state` - Complete conversation state

## Test Markers

Tests can be marked with:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.memory` - Memory module tests
- `@pytest.mark.speech` - Speech module tests
- `@pytest.mark.workflow` - Workflow tests

## Coverage Configuration

Coverage is configured in `pytest.ini`:
- Minimum coverage: 70%
- HTML reports: `htmlcov/`
- Excludes: test files, interfaces, pycache

## Notes

- All fixtures are function-scoped (fresh for each test)
- Mock clients return realistic test data without API calls
- Sample audio files are generated programmatically
- Async tests are fully supported via pytest-asyncio
