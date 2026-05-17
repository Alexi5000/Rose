# Test Infrastructure Setup

This document describes the test infrastructure for the AI Companion application.

## Directory Structure

```
tests/
├── unit/                    # Unit tests for individual modules
│   ├── __init__.py
│   ├── .gitignore
│   └── test_fixtures_setup.py  # Infrastructure validation tests
├── integration/             # Integration tests for workflows
│   ├── __init__.py
│   └── .gitignore
├── fixtures/                # Reusable test fixtures
│   ├── __init__.py
│   ├── .gitignore
│   ├── README.md
│   ├── mock_clients.py      # Mock API clients (Groq, Qdrant, ElevenLabs)
│   ├── audio_samples.py     # Sample audio files for STT testing
│   └── mock_responses.py    # Sample API responses
├── conftest.py              # Pytest configuration and shared fixtures
├── pytest.ini               # Pytest settings
└── TESTING_INFRASTRUCTURE.md  # This file
```

## Test Dependencies

The following test dependencies are configured in `pyproject.toml`:

- `pytest==7.4.4` - Test framework
- `pytest-asyncio==0.23.0` - Async test support
- `pytest-mock==3.12.0` - Mocking utilities
- `pytest-cov==4.1.0` - Coverage reporting

## Running Tests

### Run All Tests
```bash
uv run pytest
```

### Run Unit Tests Only
```bash
uv run pytest tests/unit/ -v
```

### Run Integration Tests Only
```bash
uv run pytest tests/integration/ -v
```

### Run Tests by Marker
```bash
# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Run memory-related tests
uv run pytest -m memory

# Run speech-related tests
uv run pytest -m speech
```

### Run with Coverage
```bash
uv run pytest --cov=src/ai_companion --cov-report=html
```

### Run Without Coverage
```bash
uv run pytest --no-cov
```

## Test Markers

The following pytest markers are available:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.memory` - Memory management tests
- `@pytest.mark.speech` - Speech-to-text and text-to-speech tests
- `@pytest.mark.workflow` - LangGraph workflow tests
- `@pytest.mark.smoke` - Smoke tests for deployment validation
- `@pytest.mark.e2e` - End-to-end tests using Playwright

## Available Fixtures

### Mock Clients

- `mock_groq_client` - Mock Groq client for STT and LLM
- `mock_elevenlabs_client` - Mock ElevenLabs client for TTS (Note: May not be actively used)
- `mock_qdrant_client` - Mock Qdrant client for vector store
- `mock_groq_async_client` - Async version of Groq client
- `mock_qdrant_async_client` - Async version of Qdrant client

### Audio Samples

- `sample_wav_audio` - Valid WAV format audio bytes
- `sample_mp3_audio` - Valid MP3 format audio bytes
- `sample_invalid_audio` - Invalid audio data for error testing
- `sample_empty_audio` - Empty audio data
- `sample_oversized_audio` - Oversized audio data (30MB)
- `audio_file_path` - Temporary WAV file path
- `mp3_file_path` - Temporary MP3 file path

### Mock Responses

- `mock_groq_transcription_response` - Sample Groq STT response
- `mock_groq_chat_response` - Sample Groq chat completion response
- `mock_elevenlabs_audio_response` - Sample ElevenLabs TTS response
- `mock_qdrant_search_response` - Sample Qdrant search results
- `mock_qdrant_upsert_response` - Sample Qdrant upsert response
- `mock_memory_extraction_result` - Sample memory extraction result
- `mock_router_decision` - Sample router decision
- `mock_langgraph_state` - Sample LangGraph workflow state

### Configuration

- `test_settings` - Test-specific settings that override production settings
- `mock_env_vars` - Mock environment variables for testing

## Coverage Configuration

Coverage is configured in `tests/pytest.ini`:

- **Target**: 70% overall coverage, 80% for core modules
- **Source**: `src/ai_companion`
- **Omitted**: Tests, interfaces (Chainlit, WhatsApp)
- **Reports**: HTML reports generated in `htmlcov/`

## Writing New Tests

### Unit Test Example

```python
import pytest

@pytest.mark.unit
def test_memory_extraction(mock_groq_client):
    """Test memory extraction from user message."""
    # Arrange
    message = "I'm feeling anxious about work"
    
    # Act
    result = extract_memory(message, mock_groq_client)
    
    # Assert
    assert result is not None
    assert "anxious" in result.lower()
```

### Integration Test Example

```python
import pytest

@pytest.mark.integration
@pytest.mark.asyncio
async def test_conversation_workflow(mock_groq_client, mock_qdrant_client):
    """Test complete conversation workflow."""
    # Arrange
    state = {"messages": [{"role": "user", "content": "Hello"}]}
    
    # Act
    result = await run_workflow(state)
    
    # Assert
    assert result["messages"][-1]["role"] == "assistant"
```

## Best Practices

1. **Use Fixtures**: Leverage existing fixtures instead of creating new mocks
2. **Mark Tests**: Always add appropriate markers (`@pytest.mark.unit`, etc.)
3. **Async Tests**: Use `@pytest.mark.asyncio` for async test functions
4. **Descriptive Names**: Use clear, descriptive test function names
5. **Arrange-Act-Assert**: Follow the AAA pattern for test structure
6. **Mock External APIs**: Never make real API calls in tests
7. **Test Isolation**: Each test should be independent and not rely on others

## Troubleshooting

### Import Errors

If you encounter import errors, ensure:
- The `src` directory is in the Python path (handled by `conftest.py`)
- All `__init__.py` files are present in test directories

### Fixture Not Found

If pytest can't find a fixture:
- Check that the fixture is defined in `fixtures/` directory
- Verify the fixture is listed in `pytest_plugins` in `conftest.py`
- Ensure the fixture function has the `@pytest.fixture` decorator

### Coverage Warnings

If you see "No data was collected" warnings:
- Run tests with `--no-cov` flag for fixture validation tests
- Ensure you're testing actual source code, not just fixtures

## Next Steps

After setting up the infrastructure, the next tasks are:

1. Implement unit tests for Memory Manager module
2. Implement unit tests for Speech-to-Text module
3. Implement unit tests for Text-to-Speech module
4. Implement integration tests for LangGraph workflow
5. Achieve >70% overall test coverage

## Notes

- **ElevenLabs**: Mock fixtures are provided for backward compatibility, but the service may not be actively used in production
- **Audio Files**: Sample audio files are minimal valid files for format testing, not real speech recordings
- **Test Data**: All test data is synthetic and does not contain real user information
