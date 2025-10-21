# Rose the Healer Shaman - API Documentation

## Overview

The Rose API provides a RESTful interface for voice-first therapeutic AI interactions. The API supports session management, voice processing with speech-to-text and text-to-speech, and health monitoring.

**Base URL:** `/api/v1`

**API Version:** 1.0.0

**Interactive Documentation:**
- Swagger UI: `/api/v1/docs`
- ReDoc: `/api/v1/redoc`
- OpenAPI Spec: `/api/v1/openapi.json`

## Authentication

Currently, the API does not require authentication. Rate limiting is applied per IP address.

## Rate Limiting

All endpoints are rate-limited to prevent abuse:
- Default: 10 requests per minute per IP address
- Health checks: 60 requests per minute per IP address

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

## Request Tracing

All requests receive a unique `X-Request-ID` header for tracing and debugging.

## API Versioning

The API uses URL-based versioning (`/api/v1/`). The current version is v1.

**Backward Compatibility:** Non-versioned endpoints (`/api/`) are maintained for backward compatibility but are deprecated and will be removed in a future release.

## Endpoints

### Health Check

Check system health and external service connectivity.

**Endpoint:** `GET /api/v1/health`

**Rate Limit:** 60 requests/minute

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "groq": "connected",
    "qdrant": "connected",
    "elevenlabs": "connected",
    "sqlite": "connected"
  }
}
```

**Status Values:**
- `healthy`: All services operational
- `degraded`: One or more services unavailable

**Response Codes:**
- `200 OK`: Health check completed
- `429 Too Many Requests`: Rate limit exceeded

---

### Start Session

Initialize a new healing session with Rose.

**Endpoint:** `POST /api/v1/session/start`

**Rate Limit:** 10 requests/minute

**Request Body:** None

**Response:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Session initialized. Ready to begin your healing journey with Rose."
}
```

**Response Codes:**
- `200 OK`: Session created successfully
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

**Session Features:**
- Unique UUID v4 identifier
- Conversation history tracking
- Short-term memory (recent messages)
- Long-term memory (emotional context in Qdrant)
- Automatic summarization after 20 messages
- Persists across server restarts

---

### Process Voice

Process voice input and generate audio response.

**Endpoint:** `POST /api/v1/voice/process`

**Rate Limit:** 10 requests/minute

**Request:**
- Content-Type: `multipart/form-data`
- Fields:
  - `audio` (file, required): Audio file containing voice input
  - `session_id` (string, required): Session ID from `/session/start`

**Validation Rules:**
- Audio file size: Maximum 10MB
- Audio formats: WAV, MP3, WebM, M4A, OGG
- Session ID: Valid UUID v4 format
- Processing timeout: 60 seconds maximum

**Response:**
```json
{
  "text": "I hear the pain in your words. It's okay to feel this way. Tell me more about what you're experiencing.",
  "audio_url": "/api/v1/voice/audio/550e8400-e29b-41d4-a716-446655440000",
  "session_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Response Codes:**
- `200 OK`: Voice processed successfully
- `400 Bad Request`: Invalid audio format or empty file
- `413 Payload Too Large`: Audio file exceeds 10MB
- `429 Too Many Requests`: Rate limit exceeded
- `503 Service Unavailable`: External service unavailable
- `504 Gateway Timeout`: Processing timeout (>60 seconds)
- `500 Internal Server Error`: Server error

**Processing Flow:**
1. Validate audio file size and format
2. Transcribe audio using Groq Whisper
3. Process through LangGraph workflow with memory
4. Generate empathetic response using Rose's character
5. Synthesize audio using ElevenLabs TTS
6. Return text and audio URL

---

### Get Audio

Retrieve generated audio response file.

**Endpoint:** `GET /api/v1/voice/audio/{audio_id}`

**Rate Limit:** None (public endpoint)

**Path Parameters:**
- `audio_id` (string, required): UUID v4 audio identifier

**Response:**
- Content-Type: `audio/mpeg`
- Body: MP3 audio file stream

**Response Codes:**
- `200 OK`: Audio file found and returned
- `404 Not Found`: Audio file not found or expired

**Notes:**
- Audio files are automatically deleted after 24 hours
- No caching (Cache-Control: no-cache)
- Files are stored with secure permissions

---

## Error Responses

All errors follow a standardized format:

```json
{
  "error": "validation_error",
  "message": "Audio file too large. Maximum size is 10MB",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "details": {
    "field": "audio",
    "max_size_mb": 10,
    "received_size_mb": 15.2
  }
}
```

**Error Fields:**
- `error`: Machine-readable error code
- `message`: Human-readable error message
- `request_id`: Unique request identifier for tracing
- `details`: Additional error context (optional)

**Common Error Codes:**
- `validation_error`: Request validation failed
- `service_unavailable`: External service unavailable
- `timeout_error`: Request processing timeout
- `rate_limit_exceeded`: Rate limit exceeded
- `internal_server_error`: Unexpected server error

---

## Client Examples

### JavaScript/TypeScript

```typescript
// Start session
const sessionResponse = await fetch('/api/v1/session/start', {
  method: 'POST',
});
const { session_id } = await sessionResponse.json();

// Process voice
const formData = new FormData();
formData.append('audio', audioBlob, 'recording.webm');
formData.append('session_id', session_id);

const voiceResponse = await fetch('/api/v1/voice/process', {
  method: 'POST',
  body: formData,
});
const { text, audio_url } = await voiceResponse.json();

// Play audio
const audio = new Audio(audio_url);
audio.play();
```

### Python

```python
import requests

# Start session
response = requests.post('http://localhost:8080/api/v1/session/start')
session_id = response.json()['session_id']

# Process voice
with open('recording.wav', 'rb') as audio_file:
    files = {'audio': audio_file}
    data = {'session_id': session_id}
    response = requests.post(
        'http://localhost:8080/api/v1/voice/process',
        files=files,
        data=data
    )
    result = response.json()
    print(f"Response: {result['text']}")
    print(f"Audio URL: {result['audio_url']}")
```

### cURL

```bash
# Start session
curl -X POST http://localhost:8080/api/v1/session/start

# Process voice
curl -X POST http://localhost:8080/api/v1/voice/process \
  -F "audio=@recording.wav" \
  -F "session_id=123e4567-e89b-12d3-a456-426614174000"

# Get audio
curl http://localhost:8080/api/v1/voice/audio/550e8400-e29b-41d4-a716-446655440000 \
  --output response.mp3
```

---

## Configuration

API behavior can be configured via environment variables:

```bash
# Enable/disable API documentation
ENABLE_API_DOCS=true

# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=10

# CORS origins (comma-separated)
ALLOWED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"

# Workflow timeout (seconds)
WORKFLOW_TIMEOUT_SECONDS=60

# Security headers
ENABLE_SECURITY_HEADERS=true
```

See `.env.example` for complete configuration options.

---

## Best Practices

### Session Management
- Create a new session for each user conversation
- Store session_id on the client side (localStorage or state)
- Reuse session_id for conversation continuity
- Sessions persist across server restarts

### Error Handling
- Always check response status codes
- Parse error responses for user-friendly messages
- Implement retry logic for 503 (service unavailable)
- Handle 504 (timeout) with user feedback

### Audio Processing
- Validate audio format before upload
- Show loading states during processing (can take 5-10 seconds)
- Implement fallback for TTS failures (text-only display)
- Handle network errors gracefully

### Rate Limiting
- Implement client-side rate limiting
- Show user feedback when rate limited
- Use exponential backoff for retries
- Monitor rate limit headers

---

## Support

For issues or questions:
- Check logs with request_id for debugging
- Review health check endpoint for service status
- Consult deployment documentation in `/docs`
- Check GitHub issues for known problems

---

## Changelog

### Version 1.0.0 (Current)
- Initial API release
- Session management endpoints
- Voice processing with STT/TTS
- Health monitoring
- Rate limiting and security headers
- Structured error responses
- Request tracing with request IDs
