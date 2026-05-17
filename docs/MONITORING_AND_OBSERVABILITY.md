# Monitoring and Observability Implementation

This document describes the monitoring and observability features implemented for Rose the Healer Shaman application.

## Overview

The application now includes comprehensive monitoring and observability features:
- **Structured logging** with JSON output for production
- **Request ID tracking** for distributed tracing
- **Enhanced health checks** with database verification
- **Resource limits** configured in Docker

## Structured Logging

### Configuration

Structured logging is implemented using `structlog` and configured in `src/ai_companion/core/logging_config.py`.

**Environment Variables:**
- `LOG_LEVEL`: Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: INFO
- `LOG_FORMAT`: Set output format (json or console). Default: json

**Example Configuration:**
```bash
# Production (JSON format for parsing)
LOG_LEVEL=INFO
LOG_FORMAT=json

# Development (Console format for readability)
LOG_LEVEL=DEBUG
LOG_FORMAT=console
```

### Usage

```python
from ai_companion.core.logging_config import get_logger

logger = get_logger(__name__)

# Log with structured data
logger.info("user_action", user_id="123", action="voice_input", duration_ms=250)

# Log errors with context
logger.error("api_call_failed", service="groq", error=str(e), retry_count=3)
```

### Log Format

**JSON Format (Production):**
```json
{
  "event": "user_action",
  "user_id": "123",
  "action": "voice_input",
  "duration_ms": 250,
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "logger": "ai_companion.interfaces.web.routes.voice",
  "level": "info",
  "timestamp": "2025-10-21T00:46:31.040719Z"
}
```

**Console Format (Development):**
```
2025-10-21T00:46:31.040719Z [info     ] user_action                    action=voice_input duration_ms=250 user_id=123
```

## Request ID Tracking

### Implementation

The `RequestIDMiddleware` automatically adds a unique request ID to every HTTP request.

**Features:**
- Generates UUID for each request
- Stores in `request.state.request_id` for access in route handlers
- Adds `X-Request-ID` header to all responses
- Binds to structlog context for automatic inclusion in all logs

### Usage

**In Route Handlers:**
```python
@router.post("/api/voice/process")
async def process_voice(request: Request):
    request_id = request.state.request_id
    logger.info("processing_voice", request_id=request_id)
```

**In Client Responses:**
```bash
curl -i http://localhost:8080/api/health
# Response includes:
# X-Request-ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Tracing Requests:**
All logs for a single request will include the same `request_id`, making it easy to trace the entire request lifecycle:

```bash
# Filter logs by request ID
cat logs.json | jq 'select(.request_id == "a1b2c3d4-e5f6-7890-abcd-ef1234567890")'
```

## Enhanced Health Checks

### Endpoint

`GET /api/health`

### Checks Performed

1. **Groq API** - LLM and STT service connectivity
2. **ElevenLabs** - TTS service connectivity
3. **Qdrant** - Vector database connectivity
4. **SQLite** - Short-term memory database verification (NEW)

### Response Format

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "groq": "connected",
    "elevenlabs": "connected",
    "qdrant": "connected",
    "sqlite": "connected"
  }
}
```

**Status Values:**
- `healthy`: All services connected
- `degraded`: One or more services disconnected

### Database Verification

The SQLite health check:
1. Verifies database file exists or can be created
2. Tests database connectivity with a simple query
3. Ensures data directory is writable

## Resource Limits

### Docker Configuration

**Dockerfile:**
```dockerfile
# Memory limit environment variable
ENV MEMORY_LIMIT=512m
```

**docker-compose.yml:**
```yaml
services:
  whatsapp:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

### Railway Configuration

**railway.json:**
```json
{
  "deploy": {
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

**Resource Limits:**
- Memory limits are configured in Railway dashboard
- Health check timeout: 30 seconds
- Restart policy: On failure, max 3 retries

## Monitoring Best Practices

### Log Aggregation

For production deployments, aggregate logs using:
- **Railway Logs**: Built-in log viewer with filtering
- **External Services**: Datadog, New Relic, Splunk, ELK Stack
- **Cloud Logging**: Google Cloud Logging, AWS CloudWatch

**Example: Parsing JSON Logs**
```bash
# Count errors by service
cat logs.json | jq -r 'select(.level == "error") | .service' | sort | uniq -c

# Average response times
cat logs.json | jq -r 'select(.duration_ms) | .duration_ms' | awk '{sum+=$1; count++} END {print sum/count}'

# Find slow requests
cat logs.json | jq 'select(.duration_ms > 1000)'
```

### Alerting

Set up alerts for:
- **Error Rate**: > 5% of requests failing
- **Response Time**: P95 > 2 seconds
- **Health Check**: Status = "degraded" for > 5 minutes
- **Memory Usage**: > 80% of limit

### Metrics to Track

1. **Request Metrics**
   - Request count by endpoint
   - Response time (P50, P95, P99)
   - Error rate by status code

2. **Service Metrics**
   - External API latency (Groq, ElevenLabs, Qdrant)
   - Circuit breaker state changes
   - Retry counts

3. **Resource Metrics**
   - Memory usage
   - CPU usage
   - Disk usage (for SQLite and audio files)

4. **Business Metrics**
   - Active sessions
   - Voice interactions per hour
   - Average conversation length

## Troubleshooting

### High Log Volume

If logs are too verbose:
```bash
# Set higher log level
LOG_LEVEL=WARNING
```

### Missing Request IDs

If request IDs are not appearing in logs:
1. Verify `RequestIDMiddleware` is added to app
2. Check middleware order (should be first)
3. Ensure structlog context is bound

### Health Check Failures

If health checks fail:
1. Check service connectivity (network, API keys)
2. Verify database file permissions
3. Check disk space for SQLite database
4. Review logs for specific error messages

### Performance Issues

If experiencing performance issues:
1. Check log level (DEBUG is very verbose)
2. Verify JSON rendering is not causing bottlenecks
3. Consider sampling logs in high-traffic scenarios

## Next Steps

Future enhancements for monitoring:
1. **Application Metrics**: Prometheus/StatsD integration
2. **Distributed Tracing**: OpenTelemetry integration
3. **Performance Profiling**: Add timing decorators
4. **Error Tracking**: Sentry integration
5. **Custom Dashboards**: Grafana or Railway metrics

## References

- [structlog Documentation](https://www.structlog.org/)
- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
- [Railway Observability](https://docs.railway.app/reference/observability)
