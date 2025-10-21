# Circuit Breakers and Resilience Patterns

This document describes the circuit breaker implementation and resilience patterns used in the Rose application to handle external service failures gracefully.

## Overview

Circuit breakers prevent cascading failures by detecting when external services are unavailable and failing fast instead of repeatedly attempting doomed requests. This improves system stability, reduces resource consumption, and provides better user experience during service outages.

## Implementation

### Circuit Breaker States

The circuit breaker has three states:

1. **CLOSED** (Normal Operation)
   - All requests pass through to the external service
   - Failures are counted but don't block requests
   - Transitions to OPEN when failure threshold is reached

2. **OPEN** (Service Unavailable)
   - All requests are immediately rejected with `CircuitBreakerError`
   - No requests are sent to the failing service
   - After recovery timeout, transitions to HALF_OPEN

3. **HALF_OPEN** (Testing Recovery)
   - One request is allowed through to test if service has recovered
   - If successful, transitions back to CLOSED
   - If failed, transitions back to OPEN

### Configuration

Circuit breakers are configured with:
- **failure_threshold**: Number of consecutive failures before opening (default: 5)
- **recovery_timeout**: Seconds to wait before attempting recovery (default: 60)
- **expected_exception**: Exception type to catch (default: Exception)
- **name**: Identifier for logging

### Global Circuit Breakers

Three global circuit breakers protect external services:

```python
from ai_companion.core.resilience import (
    get_groq_circuit_breaker,
    get_elevenlabs_circuit_breaker,
    get_qdrant_circuit_breaker,
)
```

#### 1. Groq API Circuit Breaker
Protects:
- Speech-to-text (Whisper)
- LLM inference (Llama models)

Configuration:
- Failure threshold: 5
- Recovery timeout: 60 seconds

#### 2. ElevenLabs API Circuit Breaker
Protects:
- Text-to-speech (Rose's voice)

Configuration:
- Failure threshold: 5
- Recovery timeout: 60 seconds

Fallback: Returns text-only response when circuit is open

#### 3. Qdrant Circuit Breaker
Protects:
- Vector memory storage
- Memory search operations

Configuration:
- Failure threshold: 5
- Recovery timeout: 60 seconds

Fallback: Continues without memory when circuit is open

## Integration Points

### Speech-to-Text (STT)

Location: `src/ai_companion/modules/speech/speech_to_text.py`

```python
# Circuit breaker wraps Groq API calls
transcription = self._circuit_breaker.call(_call_groq_api)
```

Behavior:
- If circuit is open, raises `CircuitBreakerError`
- Caught in voice endpoint and returns user-friendly error
- Existing retry logic still applies when circuit is closed

### Text-to-Speech (TTS)

Location: `src/ai_companion/modules/speech/text_to_speech.py`

```python
# Circuit breaker wraps ElevenLabs API calls
audio_bytes = self._circuit_breaker.call(_call_elevenlabs_api)
```

Behavior:
- If circuit is open, falls back to text-only response
- User receives message: "I'm having trouble with my voice right now, but I'm here: {text}"
- Graceful degradation maintains conversation continuity

### Vector Memory (Qdrant)

Location: `src/ai_companion/modules/memory/long_term/vector_store.py`

```python
# Circuit breaker wraps all Qdrant operations
results = self._circuit_breaker.call(_search)
```

Behavior:
- If circuit is open, returns empty results
- Application continues without long-term memory
- Short-term memory (SQLite) still functions normally

## Workflow-Level Error Handling

### Global Timeout Configuration

All LangGraph workflow invocations have a global timeout:

```python
# In settings.py
WORKFLOW_TIMEOUT_SECONDS: int = 60  # Default: 60 seconds
```

### Error Handling in Interfaces

#### Web API (Voice Endpoint)

Location: `src/ai_companion/interfaces/web/routes/voice.py`

```python
try:
    result = await asyncio.wait_for(
        graph.ainvoke(...),
        timeout=settings.WORKFLOW_TIMEOUT_SECONDS,
    )
except asyncio.TimeoutError:
    # Return 504 Gateway Timeout
except CircuitBreakerError:
    # Return 503 Service Unavailable
except Exception:
    # Return 503 with generic error message
```

#### Chainlit Interface

Location: `src/ai_companion/interfaces/chainlit/app.py`

```python
try:
    async with asyncio.timeout(settings.WORKFLOW_TIMEOUT_SECONDS):
        async for chunk in graph.astream(...):
            # Stream response
except asyncio.TimeoutError:
    await cl.Message(content="I'm taking longer than usual...").send()
except CircuitBreakerError:
    await cl.Message(content="I'm having trouble connecting...").send()
```

#### WhatsApp Interface

Location: `src/ai_companion/interfaces/whatsapp/whatsapp_response.py`

```python
try:
    await asyncio.wait_for(
        graph.ainvoke(...),
        timeout=settings.WORKFLOW_TIMEOUT_SECONDS,
    )
except asyncio.TimeoutError:
    await send_response(from_number, "I'm taking longer than usual...")
except CircuitBreakerError:
    await send_response(from_number, "I'm having trouble connecting...")
```

## User Experience

### Error Messages

Circuit breakers provide user-friendly error messages:

| Scenario | User Message |
|----------|-------------|
| STT circuit open | "I couldn't hear that clearly. Could you try again?" |
| TTS circuit open | "I'm having trouble with my voice right now, but I'm here: {text}" |
| Workflow timeout | "I'm taking longer than usual to respond. Please try again." |
| General circuit breaker | "I'm having trouble connecting to my services right now. Please try again in a moment." |
| Workflow failure | "I'm having trouble processing that right now. Could you try rephrasing?" |

### Graceful Degradation

The application maintains functionality even when services fail:

1. **TTS Failure**: Falls back to text-only responses
2. **Memory Failure**: Continues conversation without long-term memory
3. **Timeout**: Suggests user retry with clear feedback

## Monitoring and Logging

### Circuit Breaker Logs

Circuit breakers log state transitions:

```
INFO: GroqAPI: Attempting recovery (HALF_OPEN)
WARNING: GroqAPI: Failure 3/5 - Exception: Service unavailable
ERROR: GroqAPI: Circuit breaker OPENED after 5 failures. Will retry in 60s
INFO: GroqAPI: Recovery successful, closing circuit
```

### Workflow Error Logs

Workflow failures are logged with full context:

```python
logger.error(f"Workflow timeout after {settings.WORKFLOW_TIMEOUT_SECONDS}s for session {session_id}")
logger.error(f"Circuit breaker open during workflow: {e}")
logger.error(f"LangGraph workflow failed: {e}", exc_info=True)
```

## Testing

### Unit Tests

Location: `tests/test_circuit_breaker.py`

Tests cover:
- Circuit breaker state transitions
- Failure threshold behavior
- Recovery timeout logic
- Async function support
- Manual reset functionality
- Exception type filtering

Run tests:
```bash
uv run pytest tests/test_circuit_breaker.py -v
```

### Integration Testing

To test circuit breakers in integration:

1. **Simulate Service Failure**: Use invalid API keys or disconnect network
2. **Trigger Failures**: Make 5+ requests to open circuit
3. **Verify Fast Fail**: Subsequent requests should fail immediately
4. **Wait for Recovery**: After 60 seconds, circuit should attempt recovery
5. **Verify Recovery**: Successful request should close circuit

## Configuration

### Environment Variables

Add to `.env`:

```bash
# Workflow timeout (seconds)
WORKFLOW_TIMEOUT_SECONDS=60
```

### Tuning Circuit Breakers

To adjust circuit breaker behavior, modify in `src/ai_companion/core/resilience.py`:

```python
groq_circuit_breaker = CircuitBreaker(
    failure_threshold=5,      # Increase for more tolerance
    recovery_timeout=60,      # Increase for longer backoff
    expected_exception=Exception,
    name="GroqAPI",
)
```

## Best Practices

1. **Don't Retry on Circuit Breaker Errors**: Circuit breaker already implements retry logic
2. **Log Circuit State Changes**: Monitor for patterns indicating service issues
3. **Provide User Feedback**: Always inform users when services are degraded
4. **Implement Fallbacks**: Design graceful degradation paths
5. **Monitor Recovery**: Track how often circuits open and recovery success rate

## Future Enhancements

Potential improvements:

1. **Metrics Collection**: Track circuit breaker state changes and failure rates
2. **Dynamic Thresholds**: Adjust thresholds based on error patterns
3. **Health Check Integration**: Proactively open circuits based on health checks
4. **Bulkhead Pattern**: Isolate resources for different service calls
5. **Rate Limiting Integration**: Coordinate with rate limiters for better backpressure

## References

- Circuit Breaker Pattern: https://martinfowler.com/bliki/CircuitBreaker.html
- Resilience Patterns: https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker
- Requirements: See `.kiro/specs/deployment-readiness-review/requirements.md` (Requirement 2)
