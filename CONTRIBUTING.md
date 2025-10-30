# Contributing to Rose the Healer Shaman

Thank you for your interest in contributing to Rose! This document provides guidelines and standards for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Quality Standards](#code-quality-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Code Review Guidelines](#code-review-guidelines)
- [Common Patterns](#common-patterns)

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Node.js 18+ and npm
- `uv` package manager
- Git
- API keys for development (Groq, ElevenLabs, Qdrant)

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-companion.git
   cd ai-companion
   ```

2. **Install dependencies**
   ```bash
   uv sync
   cd frontend && npm install && cd ..
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   
   # Also configure frontend environment
   cp frontend/.env.example frontend/.env
   ```

4. **Start development servers**
   ```bash
   # Start both frontend and backend with hot reload
   python scripts/run_dev_server.py
   ```

5. **Run tests to verify setup**
   ```bash
   uv run pytest
   ```

## Code Quality Standards

### Code Formatting

We use **Ruff** for code formatting and linting. All code must pass formatting and linting checks before being merged.

**Before committing**:
```bash
# Format code
make format-fix

# Fix linting issues
make lint-fix

# Check formatting (CI will run this)
make format-check

# Check linting (CI will run this)
make lint-check
```

**Configuration**:
- Line length: 120 characters
- Import sorting: Enabled
- Target Python version: 3.12

### Type Hints

All public functions must have complete type annotations:

```python
# Good ✅
from typing import Optional, List

async def search_memories(
    query: str,
    k: int = 5,
    metadata_filter: Optional[dict] = None
) -> List[str]:
    """Search for similar memories."""
    # Implementation
    pass

# Bad ❌
async def search_memories(query, k=5, metadata_filter=None):
    # Missing type hints
    pass
```

**Type Checking**:
```bash
# Run mypy type checker
uv run mypy src/
```

### Docstrings

All public functions, classes, and modules must have docstrings:

```python
def extract_memory(message: str) -> Optional[str]:
    """Extract important information from a user message.

    Analyzes the message content to identify information worth storing
    in long-term memory, such as personal details, emotional states,
    or healing goals.

    Args:
        message: The user's message content to analyze

    Returns:
        Extracted memory text if important information found, None otherwise

    Example:
        >>> extract_memory("My name is Sarah and I live in Portland")
        "Name is Sarah, lives in Portland"
    """
    # Implementation
    pass
```

**Docstring Format**:
- Use Google-style docstrings
- Include Args, Returns, Raises sections as needed
- Add Examples for complex functions
- Keep descriptions concise but clear

### Code Organization

**Module Structure**:
```
src/ai_companion/
├── core/              # Shared utilities, prompts, exceptions
├── graph/             # LangGraph workflow (nodes, edges, state)
├── interfaces/        # User-facing interfaces (web, API)
├── modules/           # Feature modules (memory, speech, etc.)
└── settings.py        # Configuration management
```

**Import Order**:
1. Standard library imports
2. Third-party imports
3. Local application imports

```python
# Good ✅
import asyncio
from typing import Optional

from langchain_core.messages import HumanMessage
from qdrant_client import QdrantClient

from ai_companion.core.exceptions import MemoryError
from ai_companion.settings import settings
```

### Error Handling

Use the standardized error handling decorators:

```python
from ai_companion.core.error_handlers import handle_api_errors

@handle_api_errors("groq_stt", fallback_message="Could not transcribe audio")
async def transcribe_audio(audio_data: bytes) -> str:
    """Transcribe audio using Groq Whisper."""
    # Implementation
    pass
```

**Error Handling Rules**:
1. Use appropriate error handler decorator for the context
2. Provide user-friendly fallback messages
3. Never expose internal details in error messages
4. Log errors with sufficient context
5. Record metrics for monitoring

### Async/Await Patterns

Follow consistent async patterns:

```python
# Good ✅
import aiofiles

async def process_audio_file(path: str) -> bytes:
    """Process audio file asynchronously."""
    async with aiofiles.open(path, 'rb') as f:
        audio_data = await f.read()
    return await transcribe_audio(audio_data)

# Bad ❌
async def process_audio_file(path: str) -> bytes:
    """Process audio file - BLOCKS EVENT LOOP!"""
    with open(path, 'rb') as f:  # Blocking I/O in async function
        audio_data = f.read()
    return await transcribe_audio(audio_data)
```

**Async Rules**:
1. Use `async def` for functions that perform I/O
2. Always `await` async function calls
3. Use `aiofiles` for file I/O in async contexts
4. Use `asyncio.gather()` for parallel operations
5. Document any sync-to-async bridges with rationale

### Code Duplication

Avoid code duplication by extracting common logic:

```python
# Good ✅
def _check_circuit_state(self) -> None:
    """Common state checking logic."""
    # Shared implementation
    pass

def call(self, func, *args, **kwargs):
    self._check_circuit_state()
    # Sync-specific logic
    pass

async def call_async(self, func, *args, **kwargs):
    self._check_circuit_state()
    # Async-specific logic
    pass

# Bad ❌
def call(self, func, *args, **kwargs):
    # Duplicated state checking logic
    if self._state == "OPEN":
        # ...
    pass

async def call_async(self, func, *args, **kwargs):
    # Same logic duplicated
    if self._state == "OPEN":
        # ...
    pass
```

**Target**: <5% code duplication

## Testing Requirements

### Test Coverage

All new code must include tests:

- **Core modules**: >80% coverage required
- **Utility modules**: >70% coverage required
- **Integration tests**: Cover all critical workflows

**Running Tests**:
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test categories
uv run pytest tests/unit/
uv run pytest tests/integration/
```

### Test Organization

```
tests/
├── unit/                    # Unit tests for individual modules
│   ├── test_memory_manager.py
│   ├── test_speech_to_text.py
│   └── test_error_handlers.py
├── integration/             # End-to-end workflow tests
│   └── test_workflow_integration.py
├── fixtures/                # Shared test fixtures
│   ├── audio_samples.py
│   └── mock_responses.py
└── conftest.py             # Pytest configuration
```

### Writing Tests

**Unit Test Example**:
```python
import pytest
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_memory_extraction(mock_groq_client):
    """Test memory extraction from user message."""
    with patch("ai_companion.modules.memory.get_vector_store") as mock_vs:
        manager = MemoryManager()
        message = HumanMessage(content="My name is Sarah")

        await manager.extract_and_store_memory(message)

        # Verify LLM was called
        mock_groq_client.analyze.assert_called_once()
        # Verify memory was stored
        mock_vs.return_value.store_memory.assert_called_once()
```

**Integration Test Example**:
```python
@pytest.mark.asyncio
async def test_complete_conversation_workflow(mock_external_services):
    """Test end-to-end conversation flow."""
    initial_state = {
        "messages": [HumanMessage(content="I'm feeling anxious")],
        "workflow_type": "conversation"
    }

    graph = create_workflow_graph().compile()
    result = await graph.ainvoke(initial_state)

    # Verify workflow completed
    assert "messages" in result
    assert len(result["messages"]) > 1
    assert isinstance(result["messages"][-1], AIMessage)
```

**Test Guidelines**:
1. Use descriptive test names: `test_<function>_<scenario>_<expected_outcome>`
2. Mock external services (Groq, ElevenLabs, Qdrant)
3. Test both success and error cases
4. Keep tests focused and independent
5. Use fixtures for common setup

### Performance Tests

Critical operations should have performance benchmarks:

```python
import time

def test_memory_retrieval_performance():
    """Test that memory retrieval completes within 200ms."""
    manager = MemoryManager()

    start_time = time.perf_counter()
    memories = manager.get_relevant_memories("test context")
    elapsed_time = time.perf_counter() - start_time

    assert elapsed_time < 0.2, f"Memory retrieval took {elapsed_time:.3f}s (>200ms)"
```

**Performance Targets**:
- Memory extraction: <500ms
- Memory retrieval: <200ms
- STT transcription: <2s for 10s audio
- TTS synthesis: <1s for 100 words
- End-to-end workflow: <5s

## Pull Request Process

### Before Submitting

1. **Run all quality checks**:
   ```bash
   make format-fix
   make lint-fix
   uv run pytest --cov=src
   uv run mypy src/
   ```

2. **Update documentation**:
   - Add/update docstrings
   - Update README if adding features
   - Update ARCHITECTURE.md if changing patterns

3. **Write tests**:
   - Unit tests for new functions
   - Integration tests for new workflows
   - Achieve required coverage targets

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing
- [ ] Coverage targets met

## Checklist
- [ ] Code formatted with ruff
- [ ] Linting passes
- [ ] Type hints added
- [ ] Docstrings added/updated
- [ ] Documentation updated
```

### PR Guidelines

1. **Keep PRs focused**: One feature or fix per PR
2. **Write clear descriptions**: Explain what and why
3. **Reference issues**: Link to related issues
4. **Request reviews**: Tag relevant reviewers
5. **Respond to feedback**: Address all review comments

## Code Review Guidelines

### For Reviewers

**What to Check**:
- ✅ Code follows style guidelines
- ✅ Tests are comprehensive
- ✅ Documentation is clear
- ✅ No security issues
- ✅ Performance is acceptable
- ✅ Error handling is appropriate

**Review Checklist**:
```markdown
- [ ] Code quality (formatting, linting, types)
- [ ] Test coverage (>70% for new code)
- [ ] Documentation (docstrings, README updates)
- [ ] Error handling (appropriate decorators)
- [ ] Performance (no obvious bottlenecks)
- [ ] Security (no exposed secrets, proper validation)
```

### For Contributors

**Responding to Reviews**:
1. Address all comments
2. Ask questions if unclear
3. Make requested changes
4. Mark conversations as resolved
5. Request re-review when ready

## Common Patterns

### Adding a New Module

1. **Create module structure**:
   ```
   src/ai_companion/modules/new_module/
   ├── __init__.py
   ├── module_name.py
   └── utils.py
   ```

2. **Add type hints and docstrings**:
   ```python
   class NewModule:
       """Brief description of module purpose."""

       def __init__(self):
           """Initialize module."""
           pass

       async def process(self, input_data: str) -> str:
           """Process input data.

           Args:
               input_data: Data to process

           Returns:
               Processed result
           """
           pass
   ```

3. **Add error handling**:
   ```python
   from ai_companion.core.error_handlers import handle_api_errors

   @handle_api_errors("new_module")
   async def process(self, input_data: str) -> str:
       # Implementation
       pass
   ```

4. **Write tests**:
   ```python
   # tests/unit/test_new_module.py
   import pytest

   @pytest.mark.asyncio
   async def test_new_module_process():
       """Test new module processing."""
       module = NewModule()
       result = await module.process("test input")
       assert result == "expected output"
   ```

5. **Update documentation**:
   - Add module to PROJECT_STRUCTURE.md
   - Document in ARCHITECTURE.md if significant
   - Update README if user-facing

### Adding a New Graph Node

1. **Define node function**:
   ```python
   # src/ai_companion/graph/nodes.py
   from typing import Dict, Any

   async def new_node(state: AICompanionState) -> Dict[str, Any]:
       """Process state in new node.

       Args:
           state: Current workflow state

       Returns:
           State updates to apply
       """
       # Implementation
       return {"key": "value"}
   ```

2. **Add to graph**:
   ```python
   # src/ai_companion/graph/graph.py
   graph.add_node("new_node", new_node)
   graph.add_edge("previous_node", "new_node")
   ```

3. **Write integration test**:
   ```python
   @pytest.mark.asyncio
   async def test_new_node_integration():
       """Test new node in workflow."""
       initial_state = {"messages": [...]}
       graph = create_workflow_graph().compile()
       result = await graph.ainvoke(initial_state)
       # Verify node executed correctly
   ```

### Adding a New API Endpoint

1. **Define endpoint**:
   ```python
   # src/ai_companion/interfaces/web/routes/new_route.py
   from fastapi import APIRouter, HTTPException
   from pydantic import BaseModel

   router = APIRouter()

   class RequestModel(BaseModel):
       """Request model with validation."""
       field: str

   @router.post("/api/new-endpoint")
   async def new_endpoint(request: RequestModel):
       """Handle new endpoint request.

       Args:
           request: Validated request data

       Returns:
           Response data
       """
       # Implementation
       return {"result": "success"}
   ```

2. **Add to app**:
   ```python
   # src/ai_companion/interfaces/web/app.py
   from .routes.new_route import router as new_router

   app.include_router(new_router)
   ```

3. **Write API test**:
   ```python
   def test_new_endpoint(client):
       """Test new API endpoint."""
       response = client.post("/api/new-endpoint", json={"field": "value"})
       assert response.status_code == 200
       assert response.json()["result"] == "success"
   ```

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Security**: Email security@example.com (do not open public issue)
- **Chat**: Join our Discord/Slack (if available)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

## Acknowledgments

Thank you for contributing to Rose! Your efforts help make this project better for everyone.
