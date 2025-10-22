# Integration Tests

Integration tests for workflows and multi-component interactions in the AI Companion application.

## Structure

Integration tests verify:

- `test_workflow_*.py` - Complete LangGraph workflow execution
- `test_memory_integration.py` - Memory system integration (short + long term)
- `test_speech_pipeline.py` - End-to-end speech processing (STT → LLM → TTS)
- `test_api_integration.py` - API endpoint integration

## Running Integration Tests

```bash
# Run all integration tests
pytest tests/integration -m integration

# Run without real API calls (using mocks)
pytest tests/integration

# Run with real APIs (requires API keys)
pytest tests/integration --real-apis

# Run specific workflow test
pytest tests/integration/test_workflow_conversation.py
```

## Writing Integration Tests

Integration tests should:
- Test multiple components working together
- Use mock clients by default (real APIs optional)
- Verify data flow between modules
- Test realistic scenarios

Example:

```python
import pytest
from src.ai_companion.graph.graph import create_graph


@pytest.mark.integration
@pytest.mark.asyncio
async def test_conversation_workflow(
    mock_groq_client,
    mock_qdrant_client,
    sample_conversation_state
):
    """Test complete conversation workflow."""
    graph = create_graph()
    result = await graph.ainvoke(sample_conversation_state)
    
    assert result["messages"]
    assert result["workflow_type"] == "conversation"
```

## Test Markers

Use `@pytest.mark.integration` for integration tests:

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_workflow():
    pass
```

## Real API Testing

To test with real APIs (optional):

1. Set environment variables in `.env`
2. Run with `--real-apis` flag
3. Tests will skip mocks and use actual services

**Note:** Real API tests may incur costs and require valid API keys.
