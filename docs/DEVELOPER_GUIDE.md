# Developer Guide

## Overview

This guide provides comprehensive documentation for developers working on the Rose AI Companion project. It covers common patterns, best practices, troubleshooting, and examples for adding new features.

## Table of Contents

- [Getting Started](#getting-started)
- [Common Patterns](#common-patterns)
- [Error Handling](#error-handling)
- [Circuit Breakers](#circuit-breakers)
- [Async Patterns](#async-patterns)
- [Module Initialization](#module-initialization)
- [Adding New Features](#adding-new-features)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Development Environment Setup

1. **Install Prerequisites**:
   ```bash
   # Python 3.12+
   python --version

   # uv package manager
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Node.js 18+ for frontend
   node --version
   ```

2. **Clone and Setup**:
   ```bash
   git clone <repository-url>
   cd ai-companion
   uv sync
   cd frontend && npm install && cd ..
   ```

3. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Verify Setup**:
   ```bash
   uv run pytest
   make format-check
   make lint-check
   ```

### Project Structure

```
src/ai_companion/
├── core/                   # Shared utilities and patterns
│   ├── exceptions.py       # Custom exception classes
│   ├── error_handlers.py   # Error handling decorators
│   ├── resilience.py       # Circuit breaker implementation
│   ├── prompts.py          # System prompts and character cards
│   └── schedules.py        # Activity scheduling logic
├── graph/                  # LangGraph workflow
│   ├── graph.py            # Workflow graph construction
│   ├── state.py            # State schema definition
│   ├── nodes.py            # Workflow node implementations
│   ├── edges.py            # Conditional edge logic
│   └── utils/              # Graph utilities (chains, helpers)
├── interfaces/             # User-facing interfaces
│   ├── web/                # FastAPI web interface
│   └── chainlit/           # Chainlit chat interface
├── modules/                # Feature modules
│   ├── memory/             # Memory management
│   │   ├── long_term/      # Vector-based long-term memory
│   │   └── short_term/     # Conversation checkpointing
│   ├── speech/             # Speech processing
│   │   ├── speech_to_text.py
│   │   └── text_to_speech.py
│   └── image/              # Image generation (frozen)
└── settings.py             # Configuration management
```

## Common Patterns

### Error Handling Pattern

The application uses unified error handling decorators that work for both sync and async functions.

#### Basic Usage

```python
from ai_companion.core.error_handlers import handle_api_errors

@handle_api_errors("groq_stt", fallback_message="Could not transcribe audio")
async def transcribe_audio(audio_data: bytes) -> str:
    """Transcribe audio using Groq Whisper."""
    client = Groq(api_key=settings.GROQ_API_KEY)
    response = await client.audio.transcriptions.create(
        file=audio_data,
        model=settings.STT_MODEL_NAME
    )
    return response.text
```

#### Available Error Handlers

1. **handle_api_errors**: For external API calls
   ```python
   @handle_api_errors("service_name", fallback_message="Optional fallback")
   async def call_external_api():
       # Implementation
       pass
   ```

2. **handle_workflow_errors**: For LangGraph workflow operations
   ```python
   @handle_workflow_errors("node_name")
   async def workflow_node(state: AICompanionState):
       # Implementation
       pass
   ```

3. **handle_memory_errors**: For memory operations
   ```python
   @handle_memory_errors()
   def store_memory(text: str, metadata: dict):
       # Implementation
       pass
   ```

4. **handle_validation_errors**: For input validation
   ```python
   @handle_validation_errors()
   def validate_input(data: dict):
       # Implementation
       pass
   ```

#### How It Works

The error handler uses function introspection to automatically detect whether a function is sync or async:

```python
def handle_api_errors(service_name: str, fallback_message: Optional[str] = None):
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{service_name} error: {e}")
                metrics.record_error(service_name, type(e).__name__)
                return fallback_message or f"Error in {service_name}"

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{service_name} error: {e}")
                metrics.record_error(service_name, type(e).__name__)
                return fallback_message or f"Error in {service_name}"

        # Automatic detection
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator
```

**Benefits**:
- Single decorator works for both sync and async
- Consistent error logging and metrics
- User-friendly error messages
- No code duplication

## Circuit Breakers

Circuit breakers protect against cascading failures by preventing calls to failing services.

### Circuit Breaker States

```
CLOSED (Normal) → OPEN (Blocked) → HALF_OPEN (Testing) → CLOSED
```

- **CLOSED**: Normal operation, calls pass through
- **OPEN**: Service is failing, calls are blocked
- **HALF_OPEN**: Testing if service recovered, limited calls allowed

### Basic Usage

```python
from ai_companion.core.resilience import CircuitBreaker

# Create circuit breaker
groq_breaker = CircuitBreaker(
    name="groq_api",
    failure_threshold=5,      # Open after 5 failures
    recovery_timeout=60,      # Try recovery after 60 seconds
    expected_exception=GroqAPIError
)

# Use with sync function
try:
    result = groq_breaker.call(groq_client.transcribe, audio_data)
except CircuitBreakerError:
    # Circuit is open, service unavailable
    return fallback_response

# Use with async function
try:
    result = await groq_breaker.call_async(groq_client.transcribe_async, audio_data)
except CircuitBreakerError:
    # Circuit is open, service unavailable
    return fallback_response
```

### Advanced Configuration

```python
# Circuit breaker with custom settings
custom_breaker = CircuitBreaker(
    name="custom_service",
    failure_threshold=3,           # More sensitive
    recovery_timeout=30,           # Faster recovery attempts
    expected_exception=Exception,  # Catch all exceptions
    half_open_max_calls=1         # Only one test call in HALF_OPEN
)
```

### Monitoring Circuit Breaker State

```python
# Check current state
if breaker.state == "OPEN":
    logger.warning("Service is unavailable")

# Get failure count
logger.info(f"Failures: {breaker.failure_count}/{breaker.failure_threshold}")

# Get last failure time
if breaker.last_failure_time:
    time_since_failure = time.time() - breaker.last_failure_time
    logger.info(f"Last failure: {time_since_failure:.1f}s ago")
```

### Circuit Breaker Best Practices

1. **Use for External Services**: Apply to all external API calls
2. **Set Appropriate Thresholds**: Balance between sensitivity and stability
3. **Monitor State Changes**: Log state transitions for debugging
4. **Provide Fallbacks**: Always have a fallback when circuit is open
5. **Test Recovery**: Ensure HALF_OPEN state works correctly

## Async Patterns

### Async Function Guidelines

1. **Use async for I/O operations**:
   ```python
   # Good ✅
   async def fetch_data(url: str) -> dict:
       async with aiohttp.ClientSession() as session:
           async with session.get(url) as response:
               return await response.json()

   # Bad ❌
   async def fetch_data(url: str) -> dict:
       response = requests.get(url)  # Blocking I/O!
       return response.json()
   ```

2. **Use aiofiles for file operations**:
   ```python
   # Good ✅
   import aiofiles

   async def read_audio_file(path: str) -> bytes:
       async with aiofiles.open(path, 'rb') as f:
           return await f.read()

   # Bad ❌
   async def read_audio_file(path: str) -> bytes:
       with open(path, 'rb') as f:  # Blocks event loop!
           return f.read()
   ```

3. **Use asyncio.gather for parallel operations**:
   ```python
   # Good ✅
   async def process_multiple_audios(paths: List[str]) -> List[str]:
       tasks = [transcribe_audio(path) for path in paths]
       return await asyncio.gather(*tasks)

   # Bad ❌
   async def process_multiple_audios(paths: List[str]) -> List[str]:
       results = []
       for path in paths:
           result = await transcribe_audio(path)  # Sequential!
           results.append(result)
       return results
   ```

### Async Context Managers

```python
class AsyncResource:
    """Example async context manager."""

    async def __aenter__(self):
        """Async setup."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async cleanup."""
        await self.disconnect()

# Usage
async def use_resource():
    async with AsyncResource() as resource:
        await resource.do_something()
```

### Async Generators

```python
async def stream_responses(messages: List[str]) -> AsyncGenerator[str, None]:
    """Stream responses asynchronously."""
    for message in messages:
        response = await process_message(message)
        yield response

# Usage
async def consume_stream():
    async for response in stream_responses(messages):
        print(response)
```

### Common Async Pitfalls

1. **Forgetting await**:
   ```python
   # Bad ❌
   result = async_function()  # Returns coroutine, not result!

   # Good ✅
   result = await async_function()
   ```

2. **Mixing sync and async**:
   ```python
   # Bad ❌
   def sync_function():
       result = await async_function()  # SyntaxError!

   # Good ✅
   async def async_function_wrapper():
       result = await async_function()
       return result
   ```

3. **Blocking the event loop**:
   ```python
   # Bad ❌
   async def process():
       time.sleep(1)  # Blocks entire event loop!

   # Good ✅
   async def process():
       await asyncio.sleep(1)  # Yields control
   ```

## Module Initialization

### Factory Pattern

Use factory functions for singleton-like behavior:

```python
def get_speech_to_text() -> SpeechToText:
    """Get or create SpeechToText instance."""
    if not hasattr(get_speech_to_text, '_instance'):
        get_speech_to_text._instance = SpeechToText()
    return get_speech_to_text._instance

# Usage
stt = get_speech_to_text()  # Creates instance
stt2 = get_speech_to_text()  # Returns same instance
assert stt is stt2  # True
```

### Session-Scoped Instances

For Chainlit interface, use session-scoped instances:

```python
import chainlit as cl

@cl.on_chat_start
async def on_chat_start():
    """Initialize session-scoped modules."""
    # Create instances for this session
    cl.user_session.set("speech_to_text", SpeechToText())
    cl.user_session.set("text_to_speech", TextToSpeech())
    cl.user_session.set("memory_manager", MemoryManager())

@cl.on_message
async def on_message(message: cl.Message):
    """Handle message with session modules."""
    # Retrieve instances from session
    stt = cl.user_session.get("speech_to_text")
    tts = cl.user_session.get("text_to_speech")
    memory = cl.user_session.get("memory_manager")

    # Use modules
    # ...
```

### Dependency Injection

For testability, use dependency injection:

```python
class WorkflowProcessor:
    """Workflow processor with injected dependencies."""

    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        speech_to_text: Optional[SpeechToText] = None
    ):
        self.memory = memory_manager or MemoryManager()
        self.stt = speech_to_text or SpeechToText()

# Production usage
processor = WorkflowProcessor()

# Test usage with mocks
mock_memory = MagicMock()
mock_stt = MagicMock()
processor = WorkflowProcessor(
    memory_manager=mock_memory,
    speech_to_text=mock_stt
)
```

## Adding New Features

### Adding a New Module

1. **Create module structure**:
   ```bash
   mkdir -p src/ai_companion/modules/new_module
   touch src/ai_companion/modules/new_module/__init__.py
   touch src/ai_companion/modules/new_module/module_name.py
   ```

2. **Implement module with type hints**:
   ```python
   # src/ai_companion/modules/new_module/module_name.py
   from typing import Optional, List
   from ai_companion.core.error_handlers import handle_api_errors

   class NewModule:
       """Brief description of module purpose.

       This module provides functionality for...

       Attributes:
           config: Module configuration
           client: External service client

       Example:
           >>> module = NewModule()
           >>> result = await module.process("input")
       """

       def __init__(self, config: Optional[dict] = None):
           """Initialize module.

           Args:
               config: Optional configuration overrides
           """
           self.config = config or {}
           self._initialize_client()

       def _initialize_client(self) -> None:
           """Initialize external service client."""
           # Implementation
           pass

       @handle_api_errors("new_module")
       async def process(self, input_data: str) -> str:
           """Process input data.

           Args:
               input_data: Data to process

           Returns:
               Processed result

           Raises:
               ValueError: If input_data is invalid
           """
           if not input_data:
               raise ValueError("input_data cannot be empty")

           # Implementation
           result = await self._call_external_service(input_data)
           return result

       async def _call_external_service(self, data: str) -> str:
           """Call external service (private method)."""
           # Implementation
           pass
   ```

3. **Add tests**:
   ```python
   # tests/unit/test_new_module.py
   import pytest
   from unittest.mock import patch, MagicMock
   from ai_companion.modules.new_module import NewModule

   class TestNewModule:
       """Test suite for NewModule."""

       def test_initialization(self):
           """Test module initialization."""
           module = NewModule()
           assert module.config == {}

       def test_initialization_with_config(self):
           """Test module initialization with config."""
           config = {"key": "value"}
           module = NewModule(config=config)
           assert module.config == config

       @pytest.mark.asyncio
       async def test_process_success(self):
           """Test successful processing."""
           module = NewModule()
           result = await module.process("test input")
           assert result is not None

       @pytest.mark.asyncio
       async def test_process_empty_input(self):
           """Test processing with empty input."""
           module = NewModule()
           with pytest.raises(ValueError, match="cannot be empty"):
               await module.process("")

       @pytest.mark.asyncio
       async def test_process_with_mocked_service(self):
           """Test processing with mocked external service."""
           with patch.object(NewModule, '_call_external_service') as mock:
               mock.return_value = "mocked result"

               module = NewModule()
               result = await module.process("test input")

               assert result == "mocked result"
               mock.assert_called_once_with("test input")
   ```

4. **Update documentation**:
   - Add to `docs/PROJECT_STRUCTURE.md`
   - Document in `docs/ARCHITECTURE.md` if significant
   - Update `README.md` if user-facing

### Adding a New Graph Node

1. **Define node function**:
   ```python
   # src/ai_companion/graph/nodes.py
   from typing import Dict, Any
   from ai_companion.graph.state import AICompanionState
   from ai_companion.core.error_handlers import handle_workflow_errors

   @handle_workflow_errors("new_node")
   async def new_node(state: AICompanionState) -> Dict[str, Any]:
       """Process state in new node.

       This node performs...

       Args:
           state: Current workflow state containing messages, context, etc.

       Returns:
           Dictionary of state updates to apply

       Example:
           >>> state = {"messages": [...]}
           >>> updates = await new_node(state)
           >>> # updates = {"new_field": "value"}
       """
       # Extract data from state
       messages = state["messages"]
       context = state.get("context", "")

       # Process
       result = await process_data(messages, context)

       # Return state updates
       return {
           "new_field": result,
           "processed": True
       }
   ```

2. **Add to graph**:
   ```python
   # src/ai_companion/graph/graph.py
   from ai_companion.graph.nodes import new_node

   def create_workflow_graph() -> StateGraph:
       """Create the workflow graph."""
       graph = StateGraph(AICompanionState)

       # Add nodes
       graph.add_node("new_node", new_node)

       # Add edges
       graph.add_edge("previous_node", "new_node")
       graph.add_edge("new_node", "next_node")

       return graph
   ```

3. **Write integration test**:
   ```python
   # tests/integration/test_workflow_integration.py
   @pytest.mark.asyncio
   async def test_new_node_integration(mock_external_services):
       """Test new node in complete workflow."""
       # Arrange
       initial_state = {
           "messages": [HumanMessage(content="Test input")],
           "workflow_type": "conversation"
       }

       # Act
       graph = create_workflow_graph().compile()
       result = await graph.ainvoke(initial_state)

       # Assert
       assert "new_field" in result
       assert result["processed"] is True
   ```

### Adding a New API Endpoint

1. **Define endpoint**:
   ```python
   # src/ai_companion/interfaces/web/routes/new_route.py
   from fastapi import APIRouter, HTTPException, Depends
   from pydantic import BaseModel, Field
   from typing import Optional

   router = APIRouter(prefix="/api/new", tags=["new"])

   class RequestModel(BaseModel):
       """Request model with validation."""
       field: str = Field(..., min_length=1, max_length=1000)
       optional_field: Optional[str] = None

   class ResponseModel(BaseModel):
       """Response model."""
       result: str
       status: str

   @router.post("/endpoint", response_model=ResponseModel)
   async def new_endpoint(request: RequestModel):
       """Handle new endpoint request.

       Args:
           request: Validated request data

       Returns:
           Response with result and status

       Raises:
           HTTPException: If processing fails
       """
       try:
           # Process request
           result = await process_request(request.field)

           return ResponseModel(
               result=result,
               status="success"
           )
       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))
   ```

2. **Add to app**:
   ```python
   # src/ai_companion/interfaces/web/app.py
   from .routes.new_route import router as new_router

   app = FastAPI()
   app.include_router(new_router)
   ```

3. **Write API test**:
   ```python
   # tests/test_api.py
   from fastapi.testclient import TestClient

   def test_new_endpoint_success(client: TestClient):
       """Test successful API call."""
       response = client.post(
           "/api/new/endpoint",
           json={"field": "test value"}
       )

       assert response.status_code == 200
       data = response.json()
       assert data["status"] == "success"
       assert "result" in data

   def test_new_endpoint_validation_error(client: TestClient):
       """Test validation error."""
       response = client.post(
           "/api/new/endpoint",
           json={"field": ""}  # Empty field
       )

       assert response.status_code == 422  # Validation error
   ```

## Troubleshooting

### Common Issues

#### Issue: Import Errors

**Symptom**: `ModuleNotFoundError: No module named 'ai_companion'`

**Solution**:
```bash
# Ensure you're in the project root
pwd

# Install in development mode
uv sync

# Run with uv
uv run python script.py
```

#### Issue: Async Function Not Awaited

**Symptom**: `RuntimeWarning: coroutine 'function' was never awaited`

**Solution**:
```python
# Bad ❌
result = async_function()

# Good ✅
result = await async_function()
```

#### Issue: Circuit Breaker Always Open

**Symptom**: Circuit breaker stays in OPEN state

**Solution**:
```python
# Check failure threshold
logger.info(f"Failures: {breaker.failure_count}/{breaker.failure_threshold}")

# Check recovery timeout
logger.info(f"Recovery timeout: {breaker.recovery_timeout}s")

# Manually reset if needed
breaker.reset()
```

#### Issue: Tests Failing Due to Shared State

**Symptom**: Tests pass individually but fail when run together

**Solution**:
```python
# Ensure reset_singletons fixture is used
@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances."""
    # Clear caches
    get_vector_store.cache_clear()
    # Reset instances
    VectorStore._instance = None
    yield
```

#### Issue: Type Errors with Third-Party Libraries

**Symptom**: Mypy reports type errors for LangChain/Groq

**Solution**:
```python
# Add type: ignore comment with explanation
result = groq_client.transcribe(audio)  # type: ignore[arg-type]  # Groq accepts str at runtime

# Or update mypy config to ignore the module
# pyproject.toml
[[tool.mypy.overrides]]
module = ["groq.*"]
ignore_missing_imports = true
```

### Debugging Tips

1. **Use logging**:
   ```python
   import logging
   logger = logging.getLogger(__name__)

   logger.debug("Detailed debug info")
   logger.info("General information")
   logger.warning("Warning message")
   logger.error("Error occurred", exc_info=True)
   ```

2. **Use breakpoints**:
   ```python
   # Add breakpoint
   breakpoint()

   # Or use pdb
   import pdb; pdb.set_trace()
   ```

3. **Run tests with debugging**:
   ```bash
   # Stop at first failure
   uv run pytest -x

   # Enter debugger on failure
   uv run pytest --pdb

   # Show local variables
   uv run pytest -l
   ```

4. **Check circuit breaker state**:
   ```python
   logger.info(f"Circuit state: {breaker.state}")
   logger.info(f"Failures: {breaker.failure_count}")
   logger.info(f"Last failure: {breaker.last_failure_time}")
   ```

5. **Monitor async tasks**:
   ```python
   # List running tasks
   tasks = asyncio.all_tasks()
   logger.info(f"Running tasks: {len(tasks)}")

   # Cancel stuck tasks
   for task in tasks:
       if not task.done():
           task.cancel()
   ```

### Performance Debugging

1. **Profile code**:
   ```python
   import cProfile
   import pstats

   profiler = cProfile.Profile()
   profiler.enable()

   # Code to profile
   result = expensive_function()

   profiler.disable()
   stats = pstats.Stats(profiler)
   stats.sort_stats('cumulative')
   stats.print_stats(10)  # Top 10 functions
   ```

2. **Measure execution time**:
   ```python
   import time

   start = time.perf_counter()
   result = function()
   elapsed = time.perf_counter() - start
   logger.info(f"Execution time: {elapsed:.3f}s")
   ```

3. **Monitor memory usage**:
   ```python
   import psutil
   import os

   process = psutil.Process(os.getpid())
   memory_mb = process.memory_info().rss / 1024 / 1024
   logger.info(f"Memory usage: {memory_mb:.1f} MB")
   ```

## Best Practices Summary

### Code Quality

- ✅ Use type hints for all public functions
- ✅ Write comprehensive docstrings
- ✅ Follow PEP 8 style guide (enforced by ruff)
- ✅ Keep functions focused and small
- ✅ Avoid code duplication

### Error Handling

- ✅ Use appropriate error handler decorators
- ✅ Provide user-friendly error messages
- ✅ Log errors with sufficient context
- ✅ Never expose internal details to users

### Testing

- ✅ Write tests for all new code
- ✅ Achieve >70% coverage (>80% for core modules)
- ✅ Mock external dependencies
- ✅ Keep tests independent and focused

### Async Programming

- ✅ Use async for I/O operations
- ✅ Use aiofiles for file operations
- ✅ Use asyncio.gather for parallelism
- ✅ Never block the event loop

### Performance

- ✅ Use circuit breakers for external services
- ✅ Cache expensive operations
- ✅ Profile critical code paths
- ✅ Monitor performance metrics

## Resources

- [Project README](../README.md)
- [Architecture Documentation](ARCHITECTURE.md)
- [Testing Guide](../tests/TESTING_GUIDE.md)
- [Contributing Guidelines](../CONTRIBUTING.md)
- [Code Quality Report](CODE_QUALITY_REPORT.md)
- [Type Checking Status](TYPE_CHECKING_STATUS.md)

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue with reproduction steps
- **Security**: Email security@example.com
- **Documentation**: Check docs/ directory

---

**Happy coding! 🚀**
