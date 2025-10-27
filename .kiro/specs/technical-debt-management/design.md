# Design Document

## Overview

This design document outlines the approach for addressing technical debt in the AI Companion application. The solution focuses on improving test coverage, eliminating code duplication, enhancing type safety, standardizing error handling, optimizing module initialization, and improving overall code quality without disrupting existing functionality.

The design prioritizes backward compatibility and incremental improvements that can be implemented and tested independently.

## Architecture

### Current State Analysis

The application has several areas of technical debt:

1. **Test Coverage Gaps**: Core modules like Memory Manager, Speech-to-Text, and Text-to-Speech lack comprehensive unit tests
2. **Code Duplication**: Error handlers and circuit breakers have duplicated sync/async wrapper implementations
3. **Type Safety Issues**: Missing type hints in several modules, particularly in graph nodes and utility functions
4. **Module Initialization**: Global module instances in Chainlit interface create tight coupling
5. **Async Pattern Inconsistencies**: Mixed patterns for handling async operations

### Target Architecture

The improved architecture will feature:

1. **Comprehensive Test Suite**: Unit tests for all core modules with >70% coverage target
2. **Unified Error Handling**: Single implementation for sync/async error handling using introspection
3. **Complete Type Annotations**: Full type hints with mypy validation
4. **Dependency Injection**: Factory pattern for module creation with proper lifecycle management
5. **Consistent Async Patterns**: Standardized async/await usage throughout

## Components and Interfaces

### 1. Test Infrastructure

**Component**: Test Suite for Core Modules

**Purpose**: Provide comprehensive test coverage for critical application components

**Structure**:

```
tests/
├── unit/
│   ├── test_memory_manager.py      # Memory extraction, storage, retrieval
│   ├── test_speech_to_text.py      # Audio transcription with various formats
│   ├── test_text_to_speech.py      # Audio synthesis and caching
│   └── test_graph_nodes.py         # Individual node behavior
├── integration/
│   ├── test_workflow_integration.py # End-to-end workflow tests
│   └── test_memory_integration.py   # Memory system integration
└── fixtures/
    ├── audio_samples/               # Test audio files
    └── mock_responses/              # Mock API responses
```

**Key Test Scenarios**:

- Memory Manager: Extract memories from messages, store in Qdrant, retrieve relevant memories
- Speech-to-Text: Transcribe various audio formats, handle errors, retry logic
- Text-to-Speech: Synthesize audio, cache responses, fallback behavior
- Graph Nodes: Router decisions, context injection, conversation flow

### 2. Unified Error Handling

**Component**: Refactored Error Handler Decorators

**Current Issue**: Duplicated sync and async wrapper implementations in `error_handlers.py`

**Solution**: Use function introspection to determine async vs sync and apply appropriate wrapper

**Design**:

```python
def handle_api_errors(service_name: str, fallback_message: Optional[str] = None):
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Async error handling logic
            ...

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Sync error handling logic
            ...

        # Single decision point
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator
```

**Benefits**:

- Eliminates ~50% code duplication in error handlers
- Single source of truth for error handling logic
- Easier to maintain and extend

### 3. Circuit Breaker Refactoring

**Component**: Unified Circuit Breaker Implementation

**Current Issue**: Separate `call()` and `call_async()` methods with duplicated state management logic

**Solution**: Extract common state management logic into private methods

**Design**:

```python
class CircuitBreaker:
    def _check_circuit_state(self) -> None:
        """Common logic for checking and transitioning circuit state"""
        if self._state == "OPEN" and self._should_attempt_reset():
            self._state = "HALF_OPEN"
        elif self._state == "OPEN":
            raise CircuitBreakerError(...)

    def _handle_success(self) -> None:
        """Common logic for successful calls"""
        if self._state == "HALF_OPEN":
            self._state = "CLOSED"
            self._failure_count = 0

    def _handle_failure(self, exception: Exception) -> None:
        """Common logic for failed calls"""
        self._failure_count += 1
        if self._failure_count >= self.failure_threshold:
            self._state = "OPEN"
            self._last_failure_time = time.time()

    def call(self, func, *args, **kwargs):
        self._check_circuit_state()
        try:
            result = func(*args, **kwargs)
            self._handle_success()
            return result
        except self.expected_exception as e:
            self._handle_failure(e)
            raise

    async def call_async(self, func, *args, **kwargs):
        self._check_circuit_state()
        try:
            result = await func(*args, **kwargs)
            self._handle_success()
            return result
        except self.expected_exception as e:
            self._handle_failure(e)
            raise
```

**Benefits**:

- Eliminates duplicated state management logic
- Easier to add new circuit breaker features
- Consistent behavior between sync and async paths

### 4. Type Safety Enhancement

**Component**: Complete Type Annotations

**Scope**: Add type hints to all public functions and methods

**Priority Areas**:

1. `graph/nodes.py` - All node functions
2. `modules/memory/` - Memory manager and vector store
3. `modules/speech/` - STT and TTS modules
4. `graph/utils/` - Helper functions and chains

**Type Hint Standards**:

```python
from typing import Optional, List, Dict, Any
from langchain_core.messages import BaseMessage

async def memory_extraction_node(state: AICompanionState) -> Dict[str, Any]:
    """Extract and store memories with proper type hints."""
    ...

def get_relevant_memories(self, context: str) -> List[str]:
    """Retrieve memories with explicit return type."""
    ...
```

**Validation**: Run `mypy src/` to ensure type correctness

### 5. Module Initialization Pattern

**Component**: Factory Functions for Module Creation

**Current Issue**: Global module instances in `interfaces/chainlit/app.py`

**Solution**: Use factory functions or dependency injection

**Design**:

```python
# Before (global instances)
speech_to_text = SpeechToText()
text_to_speech = TextToSpeech()

# After (factory pattern)
def get_speech_to_text() -> SpeechToText:
    """Get or create SpeechToText instance."""
    if not hasattr(get_speech_to_text, '_instance'):
        get_speech_to_text._instance = SpeechToText()
    return get_speech_to_text._instance

# Or use session-scoped instances
@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("speech_to_text", SpeechToText())
    cl.user_session.set("text_to_speech", TextToSpeech())
```

**Benefits**:

- Better testability (can inject mocks)
- Clearer lifecycle management
- Reduced global state

### 6. Configuration Validation

**Component**: Enhanced Settings Validation

**Current State**: Basic Pydantic validation exists but could be more comprehensive

**Enhancements**:

1. Add validators for configuration value ranges
2. Add cross-field validation (e.g., ensure database URL is set when database type is PostgreSQL)
3. Add startup validation that tests connectivity to external services
4. Provide detailed error messages with remediation steps

**Design**:

```python
class Settings(BaseSettings):
    @field_validator("MEMORY_TOP_K")
    @classmethod
    def validate_memory_top_k(cls, v: int) -> int:
        if v < 1 or v > 20:
            raise ValueError("MEMORY_TOP_K must be between 1 and 20")
        return v

    @model_validator(mode='after')
    def validate_database_config(self) -> 'Settings':
        if self.FEATURE_DATABASE_TYPE == "postgresql" and not self.DATABASE_URL:
            raise ValueError(
                "DATABASE_URL is required when FEATURE_DATABASE_TYPE is 'postgresql'. "
                "Please set DATABASE_URL in your .env file."
            )
        return self
```

## Data Models

### Test Fixtures

**Audio Test Samples**:

- `test_audio_wav.wav` - Valid WAV format audio
- `test_audio_mp3.mp3` - Valid MP3 format audio
- `test_audio_invalid.bin` - Invalid audio data for error testing

**Mock API Responses**:

- `mock_groq_transcription.json` - Groq STT response
- `mock_elevenlabs_audio.mp3` - ElevenLabs TTS response
- `mock_qdrant_search.json` - Qdrant search results

### Type Definitions

**Common Types**:

```python
from typing import TypedDict, Literal

WorkflowType = Literal["conversation", "audio", "image"]

class MemorySearchResult(TypedDict):
    text: str
    score: float
    metadata: Dict[str, Any]
```

## Error Handling

### Error Handling Strategy

1. **External API Errors**: Use `@handle_api_errors` decorator with service-specific fallback messages
2. **Workflow Errors**: Use `@handle_workflow_errors` decorator for LangGraph execution errors
3. **Memory Errors**: Use `@handle_memory_errors` decorator with graceful degradation
4. **Validation Errors**: Use `@handle_validation_errors` decorator for user input validation

### Error Logging Standards

All error handlers should log:

- Error type and message
- Service name (for API errors)
- Function name where error occurred
- Full stack trace for unexpected errors
- Metrics recording for monitoring

### User-Facing Error Messages

- Never expose internal implementation details
- Provide actionable guidance when possible
- Use empathetic language consistent with Rose's character
- Example: "I'm having trouble with my voice right now, but I'm here: [text response]"

## Testing Strategy

### Unit Testing Approach

**Test Organization**:

- One test file per module
- Group related tests using test classes
- Use descriptive test names: `test_<function>_<scenario>_<expected_outcome>`

**Test Coverage Goals**:

- Core modules: >80% coverage
- Utility modules: >70% coverage
- Interface modules: >60% coverage (integration tests cover the rest)

**Mocking Strategy**:

- Mock external API calls (Groq, ElevenLabs, Qdrant)
- Use `pytest-mock` for function mocking
- Create reusable fixtures for common mocks

### Integration Testing Approach

**Workflow Integration Tests**:

- Test complete conversation flows
- Test memory extraction and retrieval
- Test error handling and fallback behavior
- Use real LangGraph execution with mocked external services

**Test Scenarios**:

1. Happy path: User message → Memory extraction → Router → Response
2. Audio workflow: Audio input → STT → Processing → TTS → Audio output
3. Error scenarios: API failures, circuit breaker activation, timeout handling
4. Memory scenarios: Store new memory, retrieve relevant memories, skip duplicates

### Test Fixtures and Utilities

**Pytest Fixtures**:

```python
@pytest.fixture
def mock_groq_client():
    """Mock Groq client for STT/LLM tests"""
    ...

@pytest.fixture
def mock_elevenlabs_client():
    """Mock ElevenLabs client for TTS tests"""
    ...

@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for memory tests"""
    ...

@pytest.fixture
def sample_audio_data():
    """Load sample audio file for testing"""
    ...
```

### Performance Testing

**Benchmarks**:

- Memory extraction: <500ms per message
- Memory retrieval: <200ms for top-K search
- STT transcription: <2s for 10s audio
- TTS synthesis: <1s for 100 words
- End-to-end workflow: <5s for typical conversation

## Implementation Phases

### Phase 1: Test Infrastructure (Foundation)

- Set up test directory structure
- Create test fixtures and mocks
- Implement unit tests for Memory Manager
- Implement unit tests for Speech modules

### Phase 2: Code Quality Improvements (Refactoring)

- Refactor error handlers to eliminate duplication
- Refactor circuit breakers to extract common logic
- Add type hints to all modules
- Run mypy validation

### Phase 3: Module Initialization (Architecture)

- Refactor Chainlit interface to use factory pattern
- Update graph utilities to support dependency injection
- Document module lifecycle patterns

### Phase 4: Configuration and Documentation (Polish)

- Enhance configuration validation
- Add comprehensive docstrings
- Update architecture documentation
- Create developer guide for common patterns

## Dependencies

**New Test Dependencies**:

- `pytest-asyncio` - For async test support
- `pytest-mock` - For mocking utilities
- `pytest-cov` - For coverage reporting
- `mypy` - For type checking

**No Changes to Runtime Dependencies**: All improvements use existing libraries

## Performance Considerations

**Test Execution Time**:

- Unit tests should run in <30 seconds
- Integration tests should run in <2 minutes
- Use parallel test execution with `pytest-xdist`

**Memory Usage**:

- Mock external services to avoid memory overhead
- Clean up test fixtures after each test
- Use `pytest --memray` to identify memory leaks

## Security Considerations

**Test Data**:

- Never commit real API keys to test files
- Use environment variables or test-specific keys
- Sanitize any logged data in tests

**Error Messages**:

- Ensure error messages don't expose sensitive configuration
- Validate that stack traces don't leak credentials

## Rollout Strategy

**Incremental Rollout**:

1. Implement and merge test infrastructure (no production impact)
2. Refactor error handlers with comprehensive tests (low risk)
3. Add type hints and validate with mypy (no runtime impact)
4. Refactor module initialization (requires testing in staging)
5. Deploy all changes together after full test suite passes

**Rollback Plan**:

- All changes are backward compatible
- Can revert individual commits if issues arise
- Test suite provides confidence in changes

## Success Metrics

**Code Quality Metrics**:

- Test coverage: >70% overall, >80% for core modules
- Type coverage: 100% of public functions
- Code duplication: <5% (measured by tools like `radon`)
- Mypy errors: 0

**Developer Experience Metrics**:

- Time to understand new code: Reduced by 30% (subjective survey)
- Time to add new features: Reduced by 20% (measured by story points)
- Bug fix time: Reduced by 25% (measured by issue resolution time)

**Operational Metrics**:

- No increase in error rates after deployment
- No performance degradation (response times within 5% of baseline)
- Successful deployment with zero rollbacks
