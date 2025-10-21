# Error Handling and Observability Improvements

## Overview

This document describes the error handling and observability improvements implemented for the Rose the Healer Shaman application. These improvements provide standardized error responses, performance tracking, application metrics, and configurable logging.

## Implementation Summary

### 1. Standardized Error Response Format

**Location:** `src/ai_companion/core/error_responses.py`

All API endpoints now return consistent error responses with the following structure:

```json
{
  "error": "error_code",
  "message": "User-friendly error message",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "details": null
}
```

**Features:**
- Machine-readable error codes (snake_case)
- Sanitized error messages that don't leak internal details
- Request ID for tracing
- Consistent format across all endpoints

**Error Handlers:**
- `ai_companion_error_handler`: Handles custom application exceptions
- `validation_error_handler`: Handles validation errors
- `global_exception_handler`: Catches all unhandled exceptions

**Error Codes:**
- `speech_to_text_failed`: STT conversion errors
- `text_to_speech_failed`: TTS conversion errors
- `memory_operation_failed`: Memory system errors
- `workflow_execution_failed`: LangGraph workflow errors
- `external_service_unavailable`: External API errors
- `validation_failed`: Request validation errors
- `internal_server_error`: Unexpected errors

### 2. Performance Timing Decorators

**Location:** `src/ai_companion/core/metrics.py`

The `@track_performance` decorator automatically tracks endpoint execution time and success/failure rates.

**Usage:**
```python
@track_performance("voice_processing")
async def process_voice(...):
    # Automatically tracked
```

**Metrics Collected:**
- Execution duration in milliseconds
- Success/failure counts
- Error types for failed requests

**Applied to:**
- `/api/v1/voice/process` - Voice processing endpoint
- `/api/v1/voice/audio/{id}` - Audio serving endpoint
- `/api/v1/session/start` - Session initialization
- `/api/v1/health` - Health check endpoint

### 3. Application Metrics Collection

**Location:** `src/ai_companion/core/metrics.py`

Comprehensive metrics collection for monitoring application behavior.

**Metrics Categories:**

**Counters:**
- `sessions_started`: Total sessions created
- `voice_requests_total`: Total voice processing requests
- `api_calls_{service}_{status}`: API calls by service and status
- `workflow_executions_{status}`: Workflow executions by status
- `errors_total`: Total errors by type and endpoint
- `{endpoint}_{status}`: Endpoint-specific success/failure counts

**Histograms:**
- `voice_audio_size_bytes`: Audio file sizes
- `api_duration_ms_{service}`: API call durations
- `workflow_duration_ms`: Workflow execution times
- `{endpoint}_duration_ms`: Endpoint response times

**Metrics API:**
```python
from ai_companion.core.metrics import metrics

# Record session start
metrics.record_session_started(session_id)

# Record voice request
metrics.record_voice_request(session_id, audio_size_bytes)

# Record API call
metrics.record_api_call("groq_stt", success=True, duration_ms=123.45)

# Record error
metrics.record_error("speech_to_text_failed", endpoint="voice_process")

# Record workflow execution
metrics.record_workflow_execution(session_id, duration_ms=456.78, success=True)
```

### 4. Metrics Endpoint

**Location:** `src/ai_companion/interfaces/web/routes/metrics.py`

New endpoint for retrieving application metrics:

**Endpoint:** `GET /api/v1/metrics`

**Response:**
```json
{
  "counters": {
    "sessions_started": 42,
    "voice_requests_total": 156,
    "errors_total": 3
  },
  "gauges": {},
  "histograms": {
    "voice_audio_size_bytes": {
      "count": 156,
      "min": 12345,
      "max": 987654,
      "avg": 456789
    }
  },
  "timestamp": "2025-10-21T12:34:56.789Z"
}
```

**Rate Limit:** 60 requests/minute

### 5. Configurable Log Levels

**Location:** `src/ai_companion/core/logging_config.py` (already implemented)

Log levels can be configured via environment variables:

**Environment Variables:**
- `LOG_LEVEL`: Set to DEBUG, INFO, WARNING, ERROR, or CRITICAL (default: INFO)
- `LOG_FORMAT`: Set to "json" or "console" (default: json)

**Example:**
```bash
LOG_LEVEL=DEBUG LOG_FORMAT=console python -m uvicorn ...
```

### 6. Sanitized Error Messages

All error messages are sanitized to prevent information leakage:

**Before:**
```
"detail": "Connection to database failed: psycopg2.OperationalError: could not connect to server: Connection refused"
```

**After:**
```
"error": "external_service_unavailable",
"message": "I'm having trouble connecting to my services right now. Please try again in a moment."
```

## Structured Logging

All logs are now structured with consistent fields:

**Example Log Entry:**
```json
{
  "event": "voice_processing_started",
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "audio_size_bytes": 45678,
  "timestamp": "2025-10-21T12:34:56.789Z",
  "level": "info",
  "logger": "ai_companion.interfaces.web.routes.voice"
}
```

**Key Events Logged:**
- `session_started`: New session created
- `voice_processing_started`: Voice processing initiated
- `speech_to_text_success`: STT conversion completed
- `workflow_execution_success`: Workflow completed
- `text_to_speech_success`: TTS conversion completed
- `audio_file_saved`: Audio file saved
- `voice_processing_complete`: Full request completed
- `endpoint_performance`: Performance metrics
- `metric_counter`: Counter metric updated
- `metric_histogram`: Histogram value recorded
- `api_call`: External API call completed

## Integration with Existing Code

### Voice Processing Route

The voice processing endpoint now includes:
- Performance tracking decorator
- Metrics recording for all operations
- Structured logging for all events
- Proper exception handling with custom exceptions
- Timing metrics for STT, workflow, and TTS operations

### Session Management Route

The session endpoint now includes:
- Performance tracking decorator
- Session start metrics
- Structured logging

### Health Check Route

The health check endpoint now includes:
- Performance tracking decorator
- Structured logging for service checks

## Monitoring Integration

The metrics can be consumed by monitoring systems:

**Prometheus-style scraping:**
```bash
curl http://localhost:8080/api/v1/metrics
```

**Log aggregation:**
- JSON logs can be ingested by ELK, Splunk, or CloudWatch
- Structured fields enable easy filtering and aggregation
- Request IDs enable distributed tracing

## Error Tracking

Errors are tracked with:
- Error type classification
- Endpoint attribution
- Request ID correlation
- Full stack traces in logs (not exposed to users)

## Performance Monitoring

Performance metrics enable:
- Identifying slow endpoints
- Tracking API call latencies
- Detecting performance degradation
- Capacity planning

## Best Practices

1. **Always use structured logging:**
   ```python
   logger.info("event_name", key1=value1, key2=value2)
   ```

2. **Record metrics for important operations:**
   ```python
   metrics.record_api_call("service", success=True, duration_ms=123)
   ```

3. **Use custom exceptions for domain errors:**
   ```python
   raise SpeechToTextError("Conversion failed")
   ```

4. **Apply performance tracking to endpoints:**
   ```python
   @track_performance("endpoint_name")
   async def my_endpoint(...):
   ```

5. **Never expose internal errors to users:**
   - Use sanitized error messages
   - Log full details internally
   - Return user-friendly messages

## Testing

To verify the implementation:

1. **Check imports:**
   ```bash
   python -c "from ai_companion.core.error_responses import ErrorResponse; print('OK')"
   python -c "from ai_companion.core.metrics import metrics; print('OK')"
   ```

2. **Start the application:**
   ```bash
   uvicorn ai_companion.interfaces.web.app:app --reload
   ```

3. **Test metrics endpoint:**
   ```bash
   curl http://localhost:8080/api/v1/metrics
   ```

4. **Test error handling:**
   ```bash
   # Send invalid request to trigger error
   curl -X POST http://localhost:8080/api/v1/voice/process
   ```

5. **Check logs:**
   - Verify JSON format (if LOG_FORMAT=json)
   - Verify structured fields
   - Verify request IDs

## Future Enhancements

Potential improvements:
1. Integration with Prometheus for metrics export
2. Integration with Sentry for error tracking
3. Distributed tracing with OpenTelemetry
4. Custom dashboards in Grafana
5. Alerting based on error rates and latencies
6. Metrics retention and historical analysis

## Requirements Addressed

This implementation addresses the following requirements from the deployment readiness review:

- **Requirement 2.5**: Sanitize error messages to prevent information leakage ✅
- **Requirement 4.3**: Implement application metrics collection ✅
- **Requirement 4.5**: Add performance timing for API endpoints ✅
- **Requirement 4.6**: Add configurable log levels via environment variable ✅
- **Requirement 6.2**: Standardize error response format across all endpoints ✅

## Conclusion

These improvements provide comprehensive observability and error handling for the Rose application, enabling:
- Better debugging and troubleshooting
- Performance monitoring and optimization
- Error tracking and analysis
- User-friendly error messages
- Production-ready monitoring capabilities
