# Error Handler Usage Guide

## Overview

The `src/ai_companion/core/error_handlers.py` module provides standardized error handling decorators for consistent error management across the Rose AI Companion application.

## Available Decorators

### 1. `@handle_api_errors`

Handles external API errors with consistent logging, metrics, and user-friendly messages.

**Use for:** Groq, ElevenLabs, Qdrant, and other external service calls

**Signature:**
```python
@handle_api_errors(service_name: str, fallback_message: Optional[str] = None)
```

**Parameters:**
- `service_name`: Name of the external service (e.g., "groq", "elevenlabs", "qdrant")
- `fallback_message`: Optional custom error message for users

**Example:**
```python
from ai_companion.core.error_handlers import handle_api_errors

@handle_api_errors("groq", "Speech recognition is temporarily unavailable")
async def transcribe_audio(audio_data: bytes) -> str:
    # Call Groq Whisper API
    return transcription
```

**Handles:**
- `CircuitBreakerError` → 503 Service Unavailable
- `ExternalAPIError` → 503 Service Unavailable
- Other exceptions → 500 Internal Server Error

### 2. `@handle_workflow_errors`

Handles LangGraph workflow execution errors with graceful fallbacks.

**Use for:** LangGraph workflow invocations and state management

**Signature:**
```python
@handle_workflow_errors
```

**Example:**
```python
from ai_companion.core.error_handlers import handle_workflow_errors

@handle_workflow_errors
async def execute_conversation_workflow(state: dict) -> dict:
    # Execute LangGraph workflow
    result = await graph.ainvoke(state)
    return result
```

**Handles:**
- `WorkflowError` → 500 with user-friendly message
- Other exceptions → 500 Internal Server Error

### 3. `@handle_memory_errors`

Handles memory operation errors with graceful degradation (returns None instead of failing).

**Use for:** Qdrant vector store operations, memory extraction/retrieval

**Signature:**
```python
@handle_memory_errors
```

**Example:**
```python
from ai_companion.core.error_handlers import handle_memory_errors

@handle_memory_errors
async def store_memory(text: str, metadata: dict) -> None:
    # Store in Qdrant
    await vector_store.add(text, metadata)
```

**Handles:**
- `MemoryError` → Returns None (graceful degradation)
- Other exceptions → Returns None (graceful degradation)

**Note:** This decorator allows the application to continue functioning even if memory operations fail.

### 4. `@handle_validation_errors`

Handles validation errors with clear user feedback.

**Use for:** Input validation, data format checking

**Signature:**
```python
@handle_validation_errors
```

**Example:**
```python
from ai_companion.core.error_handlers import handle_validation_errors

@handle_validation_errors
async def validate_audio_file(audio_data: bytes) -> bool:
    if len(audio_data) > MAX_SIZE:
        raise ValueError(f"Audio file too large. Maximum size is {MAX_SIZE}MB")
    return True
```

**Handles:**
- `ValueError` → 400 Bad Request with error message
- Other exceptions → Propagates unchanged

## Best Practices

### 1. Choose the Right Decorator

- **API calls** → `@handle_api_errors`
- **Workflow execution** → `@handle_workflow_errors`
- **Memory operations** → `@handle_memory_errors`
- **Input validation** → `@handle_validation_errors`

### 2. Combine Decorators When Needed

Decorators can be stacked for comprehensive error handling:

```python
@handle_validation_errors
@handle_api_errors("groq")
async def process_audio(audio_data: bytes) -> str:
    # Validation happens first
    if not audio_data:
        raise ValueError("Audio data is required")
    
    # Then API call with error handling
    return await groq_client.transcribe(audio_data)
```

### 3. Provide Context in Service Names

Use descriptive service names for better logging and debugging:

```python
# Good
@handle_api_errors("groq_stt", "Speech recognition failed")

# Better
@handle_api_errors("groq_whisper_transcription", "Unable to transcribe audio")
```

### 4. Custom Fallback Messages

Provide user-friendly fallback messages that:
- Explain what went wrong in simple terms
- Suggest what the user can do
- Maintain Rose's empathetic tone

```python
@handle_api_errors(
    "elevenlabs",
    "I'm having trouble with my voice right now, but I'm here to listen and support you."
)
async def synthesize_speech(text: str) -> bytes:
    return await tts.synthesize(text)
```

## Error Flow

### Without Decorators (Before)
```python
async def transcribe_audio(audio_data: bytes) -> str:
    try:
        return await groq_client.transcribe(audio_data)
    except CircuitBreakerError as e:
        logger.error(f"Circuit breaker open: {e}")
        metrics.record_error("groq_circuit_breaker_open")
        raise HTTPException(status_code=503, detail="Service unavailable")
    except ExternalAPIError as e:
        logger.error(f"API error: {e}", exc_info=True)
        metrics.record_error("groq_api_error")
        raise HTTPException(status_code=503, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        metrics.record_error("groq_unexpected_error")
        raise HTTPException(status_code=500, detail="Internal error")
```

### With Decorators (After)
```python
@handle_api_errors("groq", "Speech recognition is temporarily unavailable")
async def transcribe_audio(audio_data: bytes) -> str:
    return await groq_client.transcribe(audio_data)
```

## Metrics and Logging

All decorators automatically:
- Log errors with appropriate levels (warning/error)
- Record metrics using `metrics.record_error()`
- Include context (service name, function name, error details)
- Provide stack traces for unexpected errors

**Logged Information:**
- Service name
- Function name
- Error type and message
- Stack trace (for unexpected errors)

**Recorded Metrics:**
- `{service}_circuit_breaker_open`
- `{service}_api_error`
- `{service}_unexpected_error`
- `workflow_execution_failed`
- `memory_operation_failed`
- `validation_error`

## Migration Guide

### Step 1: Identify Error-Prone Functions

Look for functions that:
- Call external APIs (Groq, ElevenLabs, Qdrant)
- Execute LangGraph workflows
- Perform memory operations
- Validate user input

### Step 2: Add Appropriate Decorator

```python
# Before
async def call_groq_api(prompt: str) -> str:
    try:
        response = await groq_client.chat(prompt)
        return response
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        raise HTTPException(status_code=503, detail="Service error")

# After
@handle_api_errors("groq", "AI service is temporarily unavailable")
async def call_groq_api(prompt: str) -> str:
    response = await groq_client.chat(prompt)
    return response
```

### Step 3: Remove Redundant Error Handling

The decorator handles:
- Logging
- Metrics
- HTTPException conversion
- User-friendly messages

You can remove this boilerplate code.

### Step 4: Test Error Scenarios

Verify that:
- Errors are logged correctly
- Metrics are recorded
- Users receive appropriate messages
- Circuit breakers work as expected

## Examples by Module

### Speech Module
```python
from ai_companion.core.error_handlers import handle_api_errors, handle_validation_errors

@handle_validation_errors
@handle_api_errors("groq_stt", "Unable to transcribe audio")
async def transcribe(audio_data: bytes) -> str:
    if not audio_data:
        raise ValueError("Audio data is required")
    return await groq_client.transcribe(audio_data)

@handle_api_errors("elevenlabs_tts", "Unable to generate audio response")
async def synthesize(text: str) -> bytes:
    return await elevenlabs_client.synthesize(text)
```

### Memory Module
```python
from ai_companion.core.error_handlers import handle_memory_errors

@handle_memory_errors
async def store_memory(text: str, metadata: dict) -> None:
    await qdrant_client.upsert(text, metadata)

@handle_memory_errors
def retrieve_memories(query: str, top_k: int = 5) -> list:
    return qdrant_client.search(query, limit=top_k)
```

### Workflow Module
```python
from ai_companion.core.error_handlers import handle_workflow_errors

@handle_workflow_errors
async def execute_conversation(state: dict, config: dict) -> dict:
    result = await graph.ainvoke(state, config)
    return result
```

## Troubleshooting

### Decorator Not Working

**Issue:** Errors not being caught by decorator

**Solution:** Ensure the decorator is applied to the correct function and that exceptions are being raised (not caught internally).

### Wrong HTTP Status Code

**Issue:** Getting 500 instead of 503 for API errors

**Solution:** Ensure you're raising `ExternalAPIError` or `CircuitBreakerError` from your API calls.

### Metrics Not Recording

**Issue:** Error metrics not appearing in logs

**Solution:** Verify that `metrics.record_error()` is imported and configured correctly.

## Related Documentation

- [Error Handling and Observability](ERROR_HANDLING_AND_OBSERVABILITY.md)
- [Circuit Breakers](CIRCUIT_BREAKERS.md)
- [API Design Verification](API_DESIGN_VERIFICATION.md)
- [Code Quality Improvements](CODE_QUALITY_IMPROVEMENTS.md)
