# Design Document

## Overview

This design outlines the migration from ElevenLabs TTS to PlayAI TTS service for the AI companion application. The migration maintains the existing TTS architecture while replacing the underlying service provider. The design preserves all existing functionality including caching, circuit breaker patterns, fallback mechanisms, and the therapeutic voice profile optimized for Rose's character.

## Architecture

### Current Architecture
The existing TTS system consists of:
- `TextToSpeech` class in `src/ai_companion/modules/speech/text_to_speech.py`
- ElevenLabs SDK integration with voice settings
- Circuit breaker pattern for resilience
- Response caching with TTL
- Graceful fallback to text-only responses
- Settings management via Pydantic

### Target Architecture
The migrated system will:
- Replace ElevenLabs SDK with PlayAI HTTP API client
- Maintain the same `TextToSpeech` class interface
- Preserve circuit breaker, caching, and fallback patterns
- Update configuration to use PlayAI credentials
- Keep all existing method signatures unchanged

## Components and Interfaces

### 1. TextToSpeech Class Modifications

**File**: `src/ai_companion/modules/speech/text_to_speech.py`

#### Changes Required:
- Replace `from elevenlabs import ElevenLabs, Voice, VoiceSettings` with HTTP client (httpx or requests)
- Update `REQUIRED_ENV_VARS` to `["PLAYAI_API_KEY", "PLAYAI_VOICE_ID"]`
- Replace `self._client: Optional[ElevenLabs]` with HTTP client instance
- Update `client` property to initialize HTTP client instead of ElevenLabs SDK
- Modify `synthesize()` method to call PlayAI API endpoints
- Update circuit breaker name from `get_elevenlabs_circuit_breaker()` to `get_playai_circuit_breaker()`

#### PlayAI API Integration:
Based on typical TTS API patterns, the implementation will:
- Use POST requests to PlayAI's TTS endpoint
- Send JSON payload with text, voice_id, and voice settings
- Receive audio data (likely MP3 or WAV format)
- Handle authentication via API key in headers

**API Request Structure** (typical pattern):
```python
POST https://api.play.ai/v1/tts
Headers:
  Authorization: Bearer {PLAYAI_API_KEY}
  Content-Type: application/json

Body:
{
  "text": "string",
  "voice": "voice_id",
  "output_format": "mp3",
  "speed": 1.0,
  "sample_rate": 24000
}
```

#### Voice Settings Mapping:
ElevenLabs parameters need to be mapped to PlayAI equivalents:
- `stability` (0.0-1.0) → PlayAI's voice consistency parameter
- `similarity_boost` (0.0-1.0) → PlayAI's voice clarity or style parameter
- `model` → PlayAI's model selection (if available)

### 2. Settings Module Updates

**File**: `src/ai_companion/settings.py`

#### Changes Required:
- Replace `ELEVENLABS_API_KEY: str` with `PLAYAI_API_KEY: str`
- Replace `ELEVENLABS_VOICE_ID: str` with `PLAYAI_VOICE_ID: str`
- Update `TTS_MODEL_NAME` default value to PlayAI's model identifier
- Remove `ROSE_VOICE_ID` or repurpose for PlayAI voice selection
- Update field validators to check PlayAI credentials

### 3. Circuit Breaker Updates

**File**: `src/ai_companion/core/resilience.py`

#### Changes Required:
- Add `get_playai_circuit_breaker()` function
- Configure circuit breaker with appropriate thresholds for PlayAI API
- Remove or deprecate `get_elevenlabs_circuit_breaker()`

### 4. Environment Configuration

**File**: `.env.example`

#### Changes Required:
- Replace ElevenLabs configuration section with PlayAI section
- Update comments to reference PlayAI instead of ElevenLabs
- Provide example PlayAI API key format
- Update Rose-specific voice configuration comments

### 5. Documentation Updates

**Files**: `.kiro/steering/tech.md`, `.kiro/steering/product.md`

#### Changes Required:
- Update technology stack to list PlayAI instead of ElevenLabs
- Update external services section
- Revise any TTS-related examples or references

## Data Models

### HTTP Client Configuration
```python
class PlayAIClient:
    base_url: str = "https://api.play.ai/v1"
    api_key: str
    timeout: int = 30
    max_retries: int = 3
```

### TTS Request Model
```python
class TTSRequest:
    text: str
    voice: str
    output_format: str = "mp3"
    speed: float = 1.0
    sample_rate: int = 24000
```

### TTS Response
- Binary audio data (bytes)
- Content-Type: audio/mpeg or audio/wav
- Response headers may include audio metadata

## Error Handling

### Error Categories

1. **Authentication Errors** (401, 403)
   - Invalid or missing API key
   - Raise `TextToSpeechError` with clear message
   - Log error for debugging

2. **Rate Limiting** (429)
   - Trigger circuit breaker
   - Use exponential backoff if retrying
   - Fall back to text-only response

3. **Service Errors** (500, 502, 503)
   - Trigger circuit breaker
   - Fall back to text-only response
   - Log error with request details

4. **Validation Errors** (400)
   - Invalid text length or parameters
   - Raise `ValueError` with specific issue
   - Do not trigger circuit breaker

5. **Network Errors**
   - Connection timeout
   - DNS resolution failure
   - Trigger circuit breaker after threshold
   - Fall back to text-only response

### Error Response Handling
```python
try:
    response = await http_client.post(...)
    response.raise_for_status()
    return response.content
except httpx.HTTPStatusError as e:
    if e.response.status_code == 401:
        raise TextToSpeechError("Invalid PlayAI API key")
    elif e.response.status_code == 429:
        raise TextToSpeechError("Rate limit exceeded")
    # ... handle other status codes
except httpx.TimeoutException:
    raise TextToSpeechError("PlayAI API timeout")
```

## Testing Strategy

### Unit Tests
- Mock PlayAI API responses
- Test successful synthesis with various parameters
- Test error handling for each error category
- Verify cache behavior (hit/miss/expiration)
- Test fallback mechanism
- Validate settings configuration

### Integration Tests
- Test actual PlayAI API calls (with test API key)
- Verify audio output format and quality
- Test voice parameter mapping
- Validate circuit breaker behavior under load
- Test cache warm-up functionality

### Manual Testing
- Compare audio quality between ElevenLabs and PlayAI
- Verify Rose's therapeutic voice characteristics
- Test in Chainlit interface
- Test in WhatsApp interface (if applicable)
- Validate error messages in UI

## Migration Strategy

### Phase 1: Preparation
1. Research PlayAI API documentation
2. Obtain PlayAI API credentials
3. Test PlayAI API with sample requests
4. Identify voice ID that matches Rose's character

### Phase 2: Implementation
1. Update settings module with PlayAI configuration
2. Implement PlayAI HTTP client in TextToSpeech class
3. Update circuit breaker configuration
4. Modify error handling for PlayAI-specific errors
5. Update environment configuration files

### Phase 3: Testing
1. Run unit tests with mocked PlayAI responses
2. Perform integration tests with actual API
3. Manual testing in both interfaces
4. Voice quality comparison

### Phase 4: Documentation
1. Update .env.example
2. Update steering documentation
3. Update README or deployment guides
4. Document any API differences or limitations

### Phase 5: Deployment
1. Update environment variables in deployment environment
2. Deploy updated code
3. Monitor for errors or issues
4. Verify TTS functionality in production

## Dependencies

### New Dependencies
- `httpx` or `requests` - HTTP client for PlayAI API calls
  - Prefer `httpx` for async support and modern API
  - Already may be in project for other HTTP needs

### Removed Dependencies
- `elevenlabs` - ElevenLabs Python SDK
  - Remove from `pyproject.toml`
  - Run `uv sync` to update lock file

### Dependency Management
```toml
# pyproject.toml changes
[project.dependencies]
- elevenlabs = "^1.0.0"  # Remove
+ httpx = "^0.27.0"      # Add if not present
```

## Performance Considerations

### API Response Time
- PlayAI API response time may differ from ElevenLabs
- Monitor latency in production
- Adjust timeout settings if needed

### Caching Strategy
- Maintain existing cache implementation
- Cache key generation remains the same
- TTL settings may need adjustment based on PlayAI performance

### Rate Limiting
- Understand PlayAI rate limits
- Configure circuit breaker thresholds accordingly
- Implement backoff strategy if needed

## Security Considerations

### API Key Management
- Store PlayAI API key in environment variables
- Never commit API keys to version control
- Use secure secret management in production (Railway secrets, etc.)

### Data Privacy
- Ensure PlayAI's data handling complies with privacy requirements
- Review PlayAI's terms of service regarding data retention
- Consider GDPR/CCPA implications for user audio data

### HTTPS/TLS
- Ensure all PlayAI API calls use HTTPS
- Validate SSL certificates
- Use secure HTTP client configuration

## Rollback Plan

### If Migration Fails
1. Revert code changes to previous commit
2. Restore ElevenLabs environment variables
3. Redeploy previous version
4. Investigate issues before retry

### Compatibility Layer (Optional)
- Consider implementing a TTS provider abstraction
- Allow switching between providers via configuration
- Useful for A/B testing or gradual migration

## Open Questions

1. **PlayAI API Endpoint**: What is the exact PlayAI TTS API endpoint URL?
2. **Voice Parameters**: How do PlayAI's voice parameters map to ElevenLabs' stability and similarity_boost?
3. **Audio Format**: What audio formats does PlayAI support (MP3, WAV, etc.)?
4. **Rate Limits**: What are PlayAI's rate limits and pricing tiers?
5. **Voice Selection**: Which PlayAI voice ID best matches Rose's therapeutic character?
6. **Model Selection**: Does PlayAI offer multiple TTS models, and which is recommended?
7. **Streaming Support**: Does PlayAI support streaming audio responses?

These questions should be answered during the implementation phase through API documentation review and testing.
