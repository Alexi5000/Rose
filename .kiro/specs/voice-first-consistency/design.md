# Design Document

## Overview

This design implements consistent voice-first responses across all user interactions in the Chainlit interface. The solution introduces a centralized TTS generation function that all message handlers use, eliminating the current workflow-type conditional logic that causes inconsistent voice responses.

## Architecture

### Current Architecture Issues

The existing Chainlit interface has two separate message handlers with different TTS logic:

1. **`on_message` (text input)**: Only generates TTS when `workflow == "audio"`, otherwise sends text-only
2. **`on_audio_end` (voice input)**: Always generates TTS by explicitly calling `text_to_speech_module.synthesize()`

This inconsistency breaks the voice-first design principle after a few exchanges when the workflow type changes.

### Proposed Architecture

```
User Input (Text/Voice/Image)
    ↓
Message Handler (on_message / on_audio_end)
    ↓
LangGraph Workflow Execution
    ↓
Response Text Generated
    ↓
[NEW] generate_voice_response() ← Centralized TTS Logic
    ↓
    ├─ Success: Audio Element + Text
    └─ Failure: Text Only (with error logging)
    ↓
Send to User
```

### Key Design Decisions

1. **Centralized TTS Function**: Create `generate_voice_response()` that encapsulates all TTS logic
2. **Always Generate Voice**: Remove workflow-type conditionals; always attempt TTS for every response
3. **Graceful Degradation**: On TTS failure, log error and send text-only response
4. **Async-First**: Use async/await throughout to prevent blocking
5. **Session-Scoped Modules**: Continue using existing factory pattern for TextToSpeech instances

## Components and Interfaces

### New Component: `generate_voice_response()`

```python
async def generate_voice_response(
    text_content: str,
    thread_id: int
) -> tuple[str, Optional[cl.Audio]]:
    """
    Generate voice response with TTS audio element.
    
    Args:
        text_content: The text response to convert to speech
        thread_id: Thread ID for logging context
        
    Returns:
        Tuple of (text_content, audio_element or None)
        
    Raises:
        No exceptions - handles all errors internally
    """
```

**Responsibilities:**
- Get session-scoped TextToSpeech instance
- Call TTS synthesis with timeout
- Create Audio element with auto-play
- Log success/failure with metrics
- Return text + audio or text-only on failure

### Modified Components

#### `on_message` Handler

**Before:**
```python
if output_state.values.get("workflow") == "audio":
    # Generate audio
elif output_state.values.get("workflow") == "image":
    # Handle image
else:
    await msg.send()  # Text only!
```

**After:**
```python
response_text = output_state["messages"][-1].content
text, audio = await generate_voice_response(response_text, thread_id)

elements = [audio] if audio else []
if output_state.values.get("workflow") == "image":
    elements.append(cl.Image(path=output_state.values["image_path"]))
    
await cl.Message(content=text, elements=elements).send()
```

#### `on_audio_end` Handler

**Before:**
```python
text_to_speech_module = get_text_to_speech()
audio_buffer = await text_to_speech_module.synthesize(...)
output_audio_el = cl.Audio(...)
await cl.Message(content=..., elements=[output_audio_el]).send()
```

**After:**
```python
response_text = output_state["messages"][-1].content
text, audio = await generate_voice_response(response_text, thread_id)

elements = [audio] if audio else []
await cl.Message(content=text, elements=elements).send()
```

## Data Models

### Audio Element Configuration

```python
cl.Audio(
    name="Rose's Voice",
    auto_play=True,
    mime="audio/mpeg3",
    content=audio_buffer  # bytes from TTS
)
```

### Logging Structure

```python
{
    "event": "tts_generation",
    "thread_id": int,
    "status": "success" | "failure" | "timeout",
    "duration_ms": float,
    "text_length": int,
    "error": str | None
}
```

## Error Handling

### TTS Synthesis Errors

**Scenario 1: ElevenLabs API Failure**
- Log error with full context
- Return text-only response
- User sees text message without audio

**Scenario 2: Timeout (>10s)**
- Cancel TTS synthesis
- Log timeout event
- Return text-only response

**Scenario 3: Circuit Breaker Open**
- Detect CircuitBreakerError
- Log circuit state
- Return text-only response
- Circuit breaker will auto-recover

**Scenario 4: Network Issues**
- Catch connection errors
- Log network failure
- Return text-only response
- Retry on next message (automatic)

### Error Recovery Strategy

1. **Immediate Fallback**: Always send text response even if TTS fails
2. **No User Interruption**: User never sees error messages about TTS
3. **Transparent Logging**: All failures logged for monitoring
4. **Auto-Recovery**: Next message attempts TTS again (no persistent failure state)

## Testing Strategy

### Unit Tests

1. **Test `generate_voice_response()` success path**
   - Mock TextToSpeech.synthesize() to return audio bytes
   - Assert Audio element created with correct properties
   - Verify logging of success metrics

2. **Test `generate_voice_response()` failure path**
   - Mock TextToSpeech.synthesize() to raise exception
   - Assert returns (text, None)
   - Verify error logging

3. **Test `generate_voice_response()` timeout**
   - Mock TextToSpeech.synthesize() to delay >10s
   - Assert timeout handling
   - Verify timeout logging

### Integration Tests

1. **Test text message with TTS**
   - Send text message via Chainlit
   - Verify response includes Audio element
   - Verify audio auto-plays

2. **Test voice message with TTS**
   - Send voice message via Chainlit
   - Verify response includes Audio element
   - Verify consistent behavior with text input

3. **Test image message with TTS**
   - Send image with text via Chainlit
   - Verify response includes both Image and Audio elements
   - Verify audio generation for image responses

4. **Test TTS failure graceful degradation**
   - Simulate ElevenLabs API failure
   - Verify text-only response sent
   - Verify no user-facing error
   - Verify error logged

### Manual Testing Checklist

- [ ] Send 10 consecutive text messages, verify all have voice
- [ ] Send 10 consecutive voice messages, verify all have voice
- [ ] Mix text and voice messages, verify consistent voice responses
- [ ] Send image with text, verify voice response
- [ ] Disconnect network, verify text fallback works
- [ ] Reconnect network, verify voice resumes
- [ ] Check logs for TTS metrics and errors
- [ ] Verify audio auto-plays in browser
- [ ] Test on multiple browsers (Chrome, Firefox, Safari)
- [ ] Verify no console errors in browser dev tools

## Performance Considerations

### TTS Generation Time

- **Target**: <3 seconds for typical response (50-200 words)
- **Timeout**: 10 seconds maximum
- **Optimization**: Use ElevenLabs turbo model (eleven_flash_v2_5)

### Memory Usage

- **Audio Buffer**: ~50-200KB per response
- **Session Storage**: Reuse TextToSpeech instance (no per-message overhead)
- **Cleanup**: Audio buffers garbage collected after message sent

### Concurrent Requests

- **Session Isolation**: Each user session has own TextToSpeech instance
- **Rate Limiting**: ElevenLabs API handles rate limiting
- **Circuit Breaker**: Protects against API overload

## Security Considerations

- **API Key Protection**: ElevenLabs API key stored in environment variables
- **Input Validation**: Text content sanitized before TTS (handled by ElevenLabs)
- **Audio Content**: No user-generated audio content stored permanently
- **Session Isolation**: Audio buffers not shared between users

## Deployment Notes

### Configuration Changes

No new environment variables required. Existing configuration sufficient:
- `ELEVENLABS_API_KEY`
- `ELEVENLABS_VOICE_ID` or `ROSE_VOICE_ID`

### Rollback Plan

If issues arise:
1. Revert Chainlit app.py to previous version
2. Restart Chainlit container
3. No database migrations required
4. No data loss risk

### Monitoring

After deployment, monitor:
- TTS success rate (should be >95%)
- TTS generation duration (should be <3s p95)
- Error logs for TTS failures
- User feedback on voice consistency

## Future Enhancements

1. **TTS Caching**: Cache audio for common responses to reduce API calls
2. **Voice Preferences**: Allow users to choose voice speed/style
3. **Streaming TTS**: Stream audio as it's generated for faster perceived response
4. **Offline Mode**: Pre-generate audio for common phrases for offline use
