# API Quick Reference

Quick reference guide for Rose Voice Companion API.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## API Version

Current version: **v1**

All endpoints use the `/api/v1/` prefix.

## Authentication

No authentication required for current version.

## Rate Limits

- Session endpoints: **10 requests/minute** per IP
- Voice endpoints: **10 requests/minute** per IP
- Health check: **60 requests/minute** per IP
- Metrics: **60 requests/minute** per IP

## Endpoints

### Session Management

#### Start Session
```http
POST /api/v1/session/start
```

**Response:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Session initialized. Rose is ready for emotional support when you are."
}
```

#### Read Memory Preferences
```http
GET /api/v1/session/{session_id}/memory-preferences
```

**Response:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "memory_mode": "enabled",
  "long_term_memory_enabled": true,
  "message": "Session memory preferences loaded."
}
```

#### Update Memory Preferences
```http
POST /api/v1/session/{session_id}/memory-preferences
Content-Type: application/json
```

**Body:**
```json
{
  "memory_mode": "session_only"
}
```

Use `enabled` to allow long-term memory for the session, or `session_only` to prevent long-term memory storage and retrieval for that session.

#### Export Session Memories
```http
GET /api/v1/session/{session_id}/memory/export
```

Exports text and metadata for memories tagged to the session. Embedding vectors are not returned.

#### Forget Session Memories
```http
POST /api/v1/session/{session_id}/memory/forget
```

Deletes long-term memories tagged to the session and invalidates cached retrievals.

### Voice Processing

#### Process Voice Input
```http
POST /api/v1/voice/process
Content-Type: multipart/form-data
```

**Parameters:**
- `audio` (file): Audio file (WAV, MP3, WebM, M4A, OGG) - max 10MB
- `session_id` (string): Session ID from `/session/start`

**Response:**
```json
{
  "text": "I hear the pain in your words. It's okay to feel this way.",
  "audio_url": "/api/v1/voice/audio/550e8400-e29b-41d4-a716-446655440000",
  "session_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

#### Get Audio File
```http
GET /api/v1/voice/audio/{audio_id}
```

**Response:** MP3 audio file (streaming)

### Health & Monitoring

#### Health Check
```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "2.1.0",
  "services": {
    "groq": "connected",
    "qdrant": "connected",
    "elevenlabs": "connected",
    "sqlite": "connected"
  }
}
```

#### Metrics
```http
GET /api/v1/metrics
```

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

## Error Responses

All errors follow this format:

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "details": {
    "field": "audio",
    "max_size_mb": 10
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `validation_error` | 400 | Invalid input parameters |
| `audio_too_large` | 413 | Audio file exceeds 10MB |
| `rate_limit_exceeded` | 429 | Too many requests |
| `service_unavailable` | 503 | External service down |
| `workflow_timeout` | 504 | Processing took too long |
| `internal_server_error` | 500 | Unexpected error |

## Example Usage

### cURL

```bash
# Start a session
SESSION_ID=$(curl -X POST http://localhost:8000/api/v1/session/start | jq -r '.session_id')

# Process voice input
curl -X POST http://localhost:8000/api/v1/voice/process \
  -F "audio=@recording.mp3" \
  -F "session_id=$SESSION_ID"

# Opt into session-only memory
curl -X POST "http://localhost:8000/api/v1/session/$SESSION_ID/memory-preferences" \
  -H "Content-Type: application/json" \
  -d '{"memory_mode":"session_only"}'

# Check health
curl http://localhost:8000/api/v1/health
```

### JavaScript (Fetch)

```javascript
// Start a session
const sessionResponse = await fetch('http://localhost:8000/api/v1/session/start', {
  method: 'POST'
});
const { session_id } = await sessionResponse.json();

// Process voice input
const formData = new FormData();
formData.append('audio', audioBlob, 'recording.webm');
formData.append('session_id', session_id);

const voiceResponse = await fetch('http://localhost:8000/api/v1/voice/process', {
  method: 'POST',
  body: formData
});
const { text, audio_url } = await voiceResponse.json();

// Play audio response
const audio = new Audio(audio_url);
audio.play();
```

### Python (requests)

```python
import requests

# Start a session
response = requests.post('http://localhost:8000/api/v1/session/start')
session_id = response.json()['session_id']

# Process voice input
with open('recording.mp3', 'rb') as audio_file:
    files = {'audio': audio_file}
    data = {'session_id': session_id}
    response = requests.post(
        'http://localhost:8000/api/v1/voice/process',
        files=files,
        data=data
    )
    result = response.json()
    print(f"Rose: {result['text']}")
```

## API Documentation

Interactive API documentation is available at:

- **Swagger UI**: `/api/v1/docs`
- **ReDoc**: `/api/v1/redoc`
- **OpenAPI JSON**: `/api/v1/openapi.json`

## Configuration

Control API behavior with environment variables:

```bash
# Enable/disable API documentation
ENABLE_API_DOCS=true

# CORS origins (comma-separated)
ALLOWED_ORIGINS="*"

# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=10

# Request size limit (bytes)
MAX_REQUEST_SIZE=10485760  # 10MB

# Workflow timeout (seconds)
WORKFLOW_TIMEOUT_SECONDS=60
```

## Backward Compatibility

Legacy endpoints without `/v1/` prefix are deprecated but still supported:

- `/api/session/start` → Use `/api/v1/session/start`
- `/api/voice/process` → Use `/api/v1/voice/process`
- `/api/health` → Use `/api/v1/health`

## Support

For issues or questions:
- Check the full documentation: `docs/API_DESIGN_VERIFICATION.md`
- Review the OpenAPI spec: `/api/v1/docs`
- Check health status: `/api/v1/health`
