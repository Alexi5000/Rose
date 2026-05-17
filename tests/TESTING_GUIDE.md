# Testing Guide

## Overview

This guide provides comprehensive documentation for the testing infrastructure, utilities, and fixtures in the Rose AI Companion project.

## Table of Contents

- [Test Organization](#test-organization)
- [Running Tests](#running-tests)
- [Test Fixtures](#test-fixtures)
- [Mocking Strategies](#mocking-strategies)
- [Writing Tests](#writing-tests)
- [Performance Testing](#performance-testing)
- [Integration Testing](#integration-testing)

## Test Organization

### Directory Structure

```
tests/
├── unit/                           # Unit tests for individual modules
│   ├── test_memory_manager.py      # Memory extraction, storage, retrieval
│   ├── test_vector_store.py        # Vector store operations
│   ├── test_speech_to_text_unit.py # STT module tests
│   ├── test_text_to_speech_unit.py # TTS module tests
│   ├── test_error_handlers.py      # Error handling decorators
│   └── test_settings.py            # Configuration validation
├── integration/                    # End-to-end workflow tests
│   └── test_workflow_integration.py # Complete workflow scenarios
├── fixtures/                       # Shared test fixtures
│   ├── audio_samples.py            # Audio file fixtures
│   └── sample_audio.py             # Audio generation utilities
├── conftest.py                     # Pytest configuration and global fixtures
├── test_circuit_breaker.py         # Circuit breaker pattern tests
├── test_performance_benchmarks.py  # Performance benchmarks
└── README.md                       # Testing documentation
```

### Test Categories

1. **Unit Tests** (`tests/unit/`):
   - Test individual functions and classes in isolation
   - Mock all external dependencies
   - Fast execution (<1s per test)
   - Target: >80% coverage for core modules

2. **Integration Tests** (`tests/integration/`):
   - Test complete workflows end-to-end
   - Mock only external services (Groq, ElevenLabs, Qdrant)
   - Use real LangGraph execution
   - Target: Cover all critical user flows

3. **Performance Tests** (`test_performance_benchmarks.py`):
   - Benchmark critical operations
   - Verify performance targets are met
   - Run separately from main test suite

## Running Tests

### Basic Commands

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_memory_manager.py

# Run specific test function
uv run pytest tests/unit/test_memory_manager.py::test_extract_memory_from_human_message

# Run tests matching pattern
uv run pytest -k "memory"

# Run with verbose output
uv run pytest -v

# Run with print statements visible
uv run pytest -s
```

### Test Categories

```bash
# Unit tests only
uv run pytest tests/unit/

# Integration tests only
uv run pytest tests/integration/

# Performance benchmarks
uv run pytest tests/test_performance_benchmarks.py

# Exclude slow tests
uv run pytest -m "not slow"
```

### Coverage Reports

```bash
# Generate HTML coverage report
uv run pytest --cov=src --cov-report=html

# View report
# Open htmlcov/index.html in browser

# Generate terminal coverage report
uv run pytest --cov=src --cov-report=term-missing

# Generate JSON coverage report (for CI)
uv run pytest --cov=src --cov-report=json
```

## Test Fixtures

### Global Fixtures (conftest.py)

#### test_settings

Provides test-specific configuration overrides:

```python
@pytest.fixture
def test_settings():
    """Test configuration overrides."""
    return {
        "GROQ_API_KEY": "test_groq_key",
        "ELEVENLABS_API_KEY": "test_elevenlabs_key",
        "QDRANT_URL": "http://localhost:6333",
        "MEMORY_TOP_K": 3,
        "SUMMARIZE_AFTER_N_MESSAGES": 5,
    }
```

**Usage**:
```python
def test_with_settings(test_settings):
    """Test using test settings."""
    assert settings.MEMORY_TOP_K == 3
```

#### reset_singletons

Automatically resets singleton instances between tests:

```python
@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances for test isolation."""
    # Runs before each test
    yield
    # Cleanup after test
```

**Purpose**: Prevents state leakage between tests when using singleton patterns.

#### mock_env_vars

Mocks environment variables for testing:

```python
@pytest.fixture
def mock_env_vars(monkeypatch, test_settings):
    """Mock environment variables."""
    for key, value in test_settings.items():
        monkeypatch.setenv(key, str(value))
```

**Usage**:
```python
def test_with_env_vars(mock_env_vars):
    """Test with mocked environment variables."""
    assert os.getenv("GROQ_API_KEY") == "test_groq_key"
```

### Audio Fixtures (fixtures/audio_samples.py)

#### sample_wav_audio

Generates a minimal valid WAV audio file:

```python
@pytest.fixture
def sample_wav_audio() -> bytes:
    """Generate minimal valid WAV audio (1 second, mono, 16kHz)."""
    # Returns WAV format bytes
```

**Usage**:
```python
def test_audio_processing(sample_wav_audio):
    """Test with WAV audio."""
    result = process_audio(sample_wav_audio)
    assert result is not None
```

#### sample_mp3_audio

Generates a minimal MP3 audio file:

```python
@pytest.fixture
def sample_mp3_audio() -> bytes:
    """Generate minimal MP3 audio."""
    # Returns MP3 format bytes
```

#### sample_invalid_audio

Generates invalid audio data for error testing:

```python
@pytest.fixture
def sample_invalid_audio() -> bytes:
    """Generate invalid audio data."""
    return b"INVALID_AUDIO_DATA"
```

#### sample_empty_audio

Generates empty audio data:

```python
@pytest.fixture
def sample_empty_audio() -> bytes:
    """Generate empty audio data."""
    return b""
```

#### sample_oversized_audio

Generates oversized audio data (30MB):

```python
@pytest.fixture
def sample_oversized_audio() -> bytes:
    """Generate oversized audio (30MB)."""
    return b"X" * (30 * 1024 * 1024)
```

#### audio_file_path

Creates a temporary WAV file:

```python
@pytest.fixture
def audio_file_path(tmp_path: Path, sample_wav_audio: bytes) -> Path:
    """Create temporary WAV file."""
    # Returns Path to temporary file
```

**Usage**:
```python
def test_file_processing(audio_file_path):
    """Test with audio file."""
    with open(audio_file_path, 'rb') as f:
        data = f.read()
    assert len(data) > 0
```

#### mp3_file_path

Creates a temporary MP3 file:

```python
@pytest.fixture
def mp3_file_path(tmp_path: Path, sample_mp3_audio: bytes) -> Path:
    """Create temporary MP3 file."""
    # Returns Path to temporary file
```

## Mocking Strategies

### Mocking External Services

#### Groq Client

```python
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def mock_groq_client():
    """Mock Groq client for LLM and STT."""
    with patch("groq.Groq") as mock:
        client = MagicMock()

        # Mock transcription
        client.audio.transcriptions.create.return_value = MagicMock(
            text="Transcribed text"
        )

        # Mock chat completion
        client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Response"))]
        )

        mock.return_value = client
        yield client
```

**Usage**:
```python
@pytest.mark.asyncio
async def test_with_groq(mock_groq_client):
    """Test with mocked Groq client."""
    stt = SpeechToText()
    result = await stt.transcribe(b"audio_data")
    assert result == "Transcribed text"
```

#### ElevenLabs Client

```python
@pytest.fixture
def mock_elevenlabs_client():
    """Mock ElevenLabs client for TTS."""
    with patch("elevenlabs.ElevenLabs") as mock:
        client = MagicMock()

        # Mock text-to-speech
        client.text_to_speech.convert.return_value = iter([b"audio_chunk"])

        mock.return_value = client
        yield client
```

#### Qdrant Client

```python
@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for vector operations."""
    with patch("qdrant_client.QdrantClient") as mock:
        client = MagicMock()

        # Mock collection operations
        client.get_collections.return_value.collections = [
            MagicMock(name="long_term_memory")
        ]

        # Mock search
        client.search.return_value = [
            MagicMock(
                score=0.95,
                payload={"text": "Memory text", "id": "mem_1"}
            )
        ]

        mock.return_value = client
        yield client
```

### Mocking LangChain Components

```python
@pytest.fixture
def mock_chat_model():
    """Mock LangChain chat model."""
    with patch("langchain_groq.ChatGroq") as mock:
        model = AsyncMock()
        model.ainvoke.return_value = AIMessage(content="AI response")
        mock.return_value = model
        yield model
```

### Mocking Circuit Breakers

```python
@pytest.fixture
def mock_circuit_breaker():
    """Mock circuit breaker for testing."""
    with patch("ai_companion.core.resilience.CircuitBreaker") as mock:
        breaker = MagicMock()

        # Pass through calls by default
        breaker.call.side_effect = lambda func, *args, **kwargs: func(*args, **kwargs)
        breaker.call_async.side_effect = lambda func, *args, **kwargs: func(*args, **kwargs)

        mock.return_value = breaker
        yield breaker
```

## Writing Tests

### Unit Test Template

```python
import pytest
from unittest.mock import patch, MagicMock

class TestModuleName:
    """Test suite for ModuleName."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        # Arrange
        module = ModuleName()
        input_data = "test input"

        # Act
        result = module.process(input_data)

        # Assert
        assert result == "expected output"

    @pytest.mark.asyncio
    async def test_async_functionality(self, mock_external_service):
        """Test async functionality with mocked service."""
        # Arrange
        module = ModuleName()
        input_data = "test input"

        # Act
        result = await module.process_async(input_data)

        # Assert
        assert result is not None
        mock_external_service.call.assert_called_once()

    def test_error_handling(self):
        """Test error handling."""
        # Arrange
        module = ModuleName()

        # Act & Assert
        with pytest.raises(ExpectedError):
            module.process(invalid_input)
```

### Integration Test Template

```python
import pytest
from langchain_core.messages import HumanMessage, AIMessage

@pytest.mark.asyncio
async def test_complete_workflow(mock_external_services):
    """Test complete workflow end-to-end."""
    # Arrange
    initial_state = {
        "messages": [HumanMessage(content="User input")],
        "workflow_type": "conversation"
    }

    # Act
    graph = create_workflow_graph().compile()
    result = await graph.ainvoke(initial_state)

    # Assert
    assert "messages" in result
    assert len(result["messages"]) > 1
    assert isinstance(result["messages"][-1], AIMessage)
    assert result["messages"][-1].content != ""
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input_data,expected_output", [
    ("test input 1", "output 1"),
    ("test input 2", "output 2"),
    ("test input 3", "output 3"),
])
def test_multiple_inputs(input_data, expected_output):
    """Test with multiple input/output pairs."""
    result = process(input_data)
    assert result == expected_output
```

### Testing Exceptions

```python
def test_raises_exception():
    """Test that function raises expected exception."""
    with pytest.raises(ValueError, match="Invalid input"):
        process_data(invalid_input)
```

### Testing Async Functions

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await async_process()
    assert result is not None
```

## Performance Testing

### Benchmark Template

```python
import time

def test_operation_performance():
    """Test that operation completes within target time."""
    # Arrange
    module = ModuleName()
    input_data = "test input"

    # Act
    start_time = time.perf_counter()
    result = module.process(input_data)
    elapsed_time = time.perf_counter() - start_time

    # Assert
    assert result is not None
    assert elapsed_time < 0.5, f"Operation took {elapsed_time:.3f}s (>500ms)"
```

### Performance Targets

- **Memory Extraction**: <500ms per message
- **Memory Retrieval**: <200ms for top-K search
- **STT Transcription**: <2s for 10s audio
- **TTS Synthesis**: <1s for 100 words
- **End-to-End Workflow**: <5s for typical conversation

## Integration Testing

### Workflow Testing

```python
@pytest.mark.asyncio
async def test_memory_workflow(mock_groq_client, mock_qdrant_client):
    """Test memory extraction and retrieval workflow."""
    # Step 1: Extract memory from message
    initial_state = {
        "messages": [HumanMessage(content="My name is Sarah")],
        "workflow_type": "conversation"
    }

    graph = create_workflow_graph().compile()
    result = await graph.ainvoke(initial_state)

    # Verify memory was extracted
    mock_qdrant_client.upsert.assert_called()

    # Step 2: Retrieve memory in next conversation
    next_state = {
        "messages": [HumanMessage(content="What's my name?")],
        "workflow_type": "conversation"
    }

    result = await graph.ainvoke(next_state)

    # Verify memory was retrieved
    mock_qdrant_client.search.assert_called()
```

### API Testing

```python
from fastapi.testclient import TestClient

def test_api_endpoint(client: TestClient):
    """Test API endpoint."""
    response = client.post(
        "/api/voice/process",
        files={"audio": ("test.wav", audio_data, "audio/wav")},
        data={"session_id": "test_session"}
    )

    assert response.status_code == 200
    assert "text" in response.json()
```

## Best Practices

### Test Naming

Use descriptive names that explain what is being tested:

```python
# Good ✅
def test_memory_extraction_from_human_message()
def test_memory_retrieval_with_empty_results()
def test_circuit_breaker_opens_after_threshold()

# Bad ❌
def test_memory()
def test_retrieval()
def test_breaker()
```

### Test Independence

Each test should be independent and not rely on other tests:

```python
# Good ✅
def test_feature_a():
    """Test feature A in isolation."""
    setup_for_test_a()
    result = feature_a()
    assert result == expected_a

def test_feature_b():
    """Test feature B in isolation."""
    setup_for_test_b()
    result = feature_b()
    assert result == expected_b

# Bad ❌
def test_feature_a():
    """Test feature A."""
    global shared_state
    shared_state = feature_a()

def test_feature_b():
    """Test feature B - depends on test_feature_a."""
    result = feature_b(shared_state)  # Depends on previous test!
```

### Arrange-Act-Assert Pattern

Structure tests clearly:

```python
def test_with_clear_structure():
    """Test with clear AAA structure."""
    # Arrange - Set up test data and mocks
    module = ModuleName()
    input_data = "test input"
    expected_output = "expected output"

    # Act - Execute the code being tested
    result = module.process(input_data)

    # Assert - Verify the results
    assert result == expected_output
```

### Mock Only What You Need

Don't over-mock:

```python
# Good ✅
def test_with_minimal_mocking(mock_external_api):
    """Mock only external dependencies."""
    # Internal logic runs normally
    result = process_data(input_data)
    assert result is not None

# Bad ❌
def test_with_excessive_mocking():
    """Mock everything including internal logic."""
    with patch("module.internal_function_1"):
        with patch("module.internal_function_2"):
            with patch("module.internal_function_3"):
                # Too much mocking - not testing real behavior
                result = process_data(input_data)
```

## Troubleshooting

### Common Issues

**Issue**: Tests fail with "fixture not found"
**Solution**: Check that fixture is defined in `conftest.py` or imported correctly

**Issue**: Async tests hang
**Solution**: Ensure `@pytest.mark.asyncio` decorator is present

**Issue**: Mocks not working
**Solution**: Verify patch path matches actual import path in code

**Issue**: Tests pass individually but fail together
**Solution**: Check for shared state or missing `reset_singletons` fixture

### Debugging Tests

```bash
# Run with debugger
uv run pytest --pdb

# Stop on first failure
uv run pytest -x

# Show local variables on failure
uv run pytest -l

# Increase verbosity
uv run pytest -vv
```

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
