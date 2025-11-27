# 🎤 Voice Interface Smoke Test Guide

## Purpose
Comprehensive smoke testing protocol to verify Rose's voice interface is 100% functional from user tap to voice response.

## Prerequisites

### Backend Requirements
- [ ] Backend server running (`uv run python -m ai_companion.interfaces.web.app`)
- [ ] Server accessible at `http://localhost:8000`
- [ ] Environment variables configured (`.env` file)
  - `GROQ_API_KEY` - For speech-to-text (Whisper)
  - `ELEVENLABS_API_KEY` - For text-to-speech
  - `ANTHROPIC_API_KEY` - For Claude LLM
  - `QDRANT_URL` - For vector memory
  - `LOG_LEVEL=INFO` - For visible logging

### Frontend Requirements
- [ ] Frontend built and served (`npm run build` in `frontend/`)
- [ ] Static files copied to `src/ai_companion/interfaces/web/static/`
- [ ] Browser with microphone support (Chrome/Edge recommended)
- [ ] HTTPS or localhost (required for microphone access)

### Browser Setup
- [ ] Open DevTools (F12)
- [ ] Console tab visible for logging
- [ ] Network tab open to monitor requests
- [ ] Allow microphone permissions when prompted

---

## Test Suite

### Test 1: Backend Health Check ✅

**Purpose:** Verify all backend services are connected and healthy

**Steps:**
1. Open terminal
2. Run: `curl http://localhost:8000/api/v1/health`
3. Verify response:
   ```json
   {
     "status": "healthy",
     "services": {
       "anthropic": "connected",
       "groq": "connected",
       "elevenlabs": "connected",
       "qdrant": "connected"
     },
     "timestamp": "2025-..."
   }
   ```

**Expected Result:**
- ✅ Status 200 OK
- ✅ All services show "connected"

**Troubleshooting:**
- ❌ Service not connected → Check API keys in `.env`
- ❌ Connection error → Verify service endpoints are accessible

**Log Markers to Watch:**
```
🏥 health_check_requested
✅ All services: connected
```

---

### Test 2: Session Creation Returns Valid UUID ✅

**Purpose:** Verify session endpoint creates unique identifiers for conversations

**Steps:**
1. Open terminal
2. Run: `curl -X POST http://localhost:8000/api/v1/session/start`
3. Verify response format:
   ```json
   {
     "session_id": "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx",
     "message": "Session started successfully"
   }
   ```
4. Run command again
5. Verify you get a DIFFERENT session_id

**Expected Result:**
- ✅ Status 200 OK
- ✅ `session_id` is valid UUID v4 format
- ✅ Each call returns unique session_id
- ✅ Message confirms session started

**Troubleshooting:**
- ❌ 500 error → Check backend logs for exceptions
- ❌ Same session_id → Check UUID generation in backend

**Log Markers to Watch:**
```
🎫 session_start_requested
✅ Session created: xxxxxxxx
```

---

### Test 3: Voice Recording Captures Audio ✅

**Purpose:** Verify frontend can access microphone and record audio

**Steps:**
1. Open browser to `http://localhost:8000`
2. Open DevTools Console (F12 → Console)
3. Click/tap screen to start voice session
4. Grant microphone permission when prompted
5. Watch console for logs
6. Speak clearly: "Hello Rose, can you hear me?"
7. Wait for silence detection to stop recording (~2 seconds of silence)

**Expected Console Logs:**
```
🎤 Starting voice session
🎫 No existing session - creating new one...
📤 API Request: POST /api/v1/session/start
✅ API Response: 200 /api/v1/session/start
✅ Session created: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
✅ Session established: xxxxxxxx...
🎙️ Requesting microphone access...
✅ Microphone access granted
✅ Voice session fully initialized and ready
🔴 Starting recording
⏹️ Recording stopped - Duration: XXXXms
📦 Audio blob created: XX.XX KB
📤 Sending to backend with session: xxxxxxxx...
```

**Expected Result:**
- ✅ Session created before microphone access
- ✅ Microphone permission granted
- ✅ Recording starts when you speak
- ✅ Recording stops after silence
- ✅ Audio blob created (> 10 KB for 5+ seconds of speech)

**Troubleshooting:**
- ❌ Microphone permission denied → Check browser settings
- ❌ Recording doesn't start → Check VAD thresholds in `voice.ts`
- ❌ Recording too short → Speak louder or adjust `RMS_ACTIVATION_THRESHOLD`
- ❌ No session created → Check network tab for 422 errors

**Log Markers to Watch:**
```
🎤 Starting voice session
🎫 Creating new session...
✅ Session established
🎙️ Requesting microphone access
✅ Microphone access granted
🔴 Starting recording
⏹️ Recording stopped
📦 Audio blob created
```

---

### Test 4: Backend Processes Voice with Session ✅

**Purpose:** Verify backend receives audio, transcribes, generates response, and creates TTS

**Steps:**
1. Continue from Test 3 (after speaking)
2. Watch console logs for API request/response
3. Watch Network tab for `/api/v1/voice/process` request
4. Verify request includes:
   - `audio` file (multipart/form-data)
   - `session_id` field
5. Wait for response (~5-20 seconds)

**Expected Console Logs:**
```
🎤 Sending audio: XX.XX KB (session: xxxxxxxx...)
📤 API Request: POST /api/v1/voice/process
✅ API Response: 200 /api/v1/voice/process
💬 Transcription: "Hello Rose, can you hear me?"
🔊 Audio URL: /api/v1/voice/audio/xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
✅ Response received from Rose
```

**Expected Backend Logs (Terminal):**
```json
{
  "event": "🎤 voice_processing_started",
  "session_id": "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx",
  "audio_size_bytes": XXXXX,
  "timestamp": "2025-..."
}
{
  "event": "✅ speech_to_text_succeeded",
  "transcription": "Hello Rose, can you hear me?",
  "duration_ms": XXXX
}
{
  "event": "✅ workflow_execution_succeeded",
  "duration_ms": XXXX
}
{
  "event": "✅ text_to_speech_succeeded",
  "text_length": XX,
  "duration_ms": XXXX
}
{
  "event": "✅ voice_processing_complete",
  "total_duration_ms": XXXX
}
```

**Expected Result:**
- ✅ Status 200 OK
- ✅ Request includes `session_id` (NOT undefined)
- ✅ Transcription matches what you said
- ✅ Audio URL returned
- ✅ Response time < 30 seconds

**Troubleshooting:**
- ❌ 422 Unprocessable Entity → Session ID missing (check frontend logs)
- ❌ 400 Bad Request → Audio format not supported
- ❌ 413 Payload Too Large → Recording too long (> 10 MB)
- ❌ 500 Internal Server Error → Check backend logs for service failures
- ❌ Transcription empty → Audio too quiet or corrupted
- ❌ Timeout → Check API keys and service connectivity

**Network Tab Checks:**
- Request Headers: `Content-Type: multipart/form-data`
- Form Data: `audio` (blob), `session_id` (string)
- Response: JSON with `text`, `audio_url`, `session_id`

---

### Test 5: Audio URL Returns Valid MP3 ✅

**Purpose:** Verify TTS audio file is saved and accessible

**Steps:**
1. Copy the `audio_url` from Test 4 console logs
   - Example: `/api/v1/voice/audio/xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`
2. Open new browser tab
3. Navigate to: `http://localhost:8000/api/v1/voice/audio/xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`
4. Verify audio file downloads or plays

**Alternative Test (cURL):**
```bash
curl -I http://localhost:8000/api/v1/voice/audio/xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
```

**Expected Result:**
- ✅ Status 200 OK
- ✅ Content-Type: `audio/mpeg`
- ✅ Content-Length: > 10000 bytes
- ✅ Audio plays Rose's voice responding

**Troubleshooting:**
- ❌ 404 Not Found → Audio file not saved (check disk space and permissions)
- ❌ 500 Error → File corruption or read error
- ❌ Audio doesn't play → Check browser audio codec support

**Log Markers to Watch:**
```
audio_file_saved (backend)
audio_file_served (backend)
```

---

### Test 6: Browser Plays Audio Successfully ✅

**Purpose:** Verify frontend fetches and plays Rose's voice response

**Steps:**
1. Continue from Test 4
2. Wait for audio to auto-play
3. Watch console for playback logs
4. Listen for Rose's voice through speakers/headphones
5. Observe shader background reacting to audio amplitude

**Expected Console Logs:**
```
🔊 Loading Rose audio: /api/v1/voice/audio/xxxxxxxx...
✅ Rose audio loaded and playing
🎵 Rose audio ended
```

**Expected Result:**
- ✅ Audio loads within 2 seconds
- ✅ Audio plays automatically
- ✅ You hear Rose's voice clearly
- ✅ Shader background pulses with audio (visual feedback)
- ✅ Playback completes without errors

**Troubleshooting:**
- ❌ Audio doesn't autoplay → Check browser autoplay policy
- ❌ No sound → Check system volume and browser audio settings
- ❌ Shader doesn't react → Check amplitude analysis in `useRoseAudio.ts`
- ❌ CORS error → Check audio URL is same-origin

**Log Markers to Watch:**
```
🔊 Loading Rose audio
✅ Rose audio loaded and playing
🎵 Rose audio ended
```

---

### Test 7: End-to-End Voice Conversation Flow ✅

**Purpose:** Verify complete multi-turn conversation works seamlessly

**Steps:**
1. Open fresh browser tab to `http://localhost:8000`
2. Open DevTools Console
3. Click screen to start session
4. **Turn 1:** Say "Hello Rose, my name is [Your Name]"
5. Wait for Rose to respond
6. Listen to her greeting
7. **Turn 2:** After audio ends, screen is still active - say "How are you today?"
8. Wait for response
9. Listen to her reply
10. **Turn 3:** Say "Thank you Rose, goodbye"
11. Wait for final response
12. Tap screen again to stop session

**Expected Flow:**
```
[User taps screen]
  → 🎫 Session created: xxxxxxxx...
  → 🎙️ Microphone access granted
  → ✅ Voice session ready

[User speaks: "Hello Rose, my name is Alex"]
  → 🔴 Recording started
  → ⏹️ Recording stopped (silence detected)
  → 📤 Sending to backend
  → 💬 Transcription: "Hello Rose, my name is Alex"
  → 🔊 Audio URL received
  → [Rose responds with voice]

[User speaks: "How are you today?"]
  → 🔴 Recording started
  → ⏹️ Recording stopped
  → 📤 Sending to backend (SAME session_id)
  → 💬 Transcription: "How are you today?"
  → 🔊 Audio URL received
  → [Rose responds, remembering your name!]

[User speaks: "Thank you Rose, goodbye"]
  → 🔴 Recording started
  → ⏹️ Recording stopped
  → 📤 Sending to backend (SAME session_id)
  → 💬 Transcription: "Thank you Rose, goodbye"
  → 🔊 Audio URL received
  → [Rose responds with personalized goodbye]

[User taps screen to stop]
  → ⏹️ Voice session stopped
  → Session remains in state (can resume if tap again)
```

**Expected Result:**
- ✅ Same `session_id` used for all turns
- ✅ Rose remembers context from previous turns (e.g., your name)
- ✅ Total round-trip time per turn: 5-20 seconds
- ✅ No 422 errors (all requests include session_id)
- ✅ Smooth transitions between listening and responding
- ✅ Inactivity timeout stops session after 30s of no speech

**Conversation Context Verification:**
In Turn 2 or 3, Rose should reference something from Turn 1 (like your name). This proves:
- Session ID is working
- LangGraph workflow maintains conversation state
- Memory is functioning

**Troubleshooting:**
- ❌ Rose doesn't remember previous turns → Check session_id consistency
- ❌ 422 error on Turn 2+ → Session ID lost, check state management
- ❌ Each turn creates new session → Frontend not persisting session_id
- ❌ Slow responses (> 30s) → Check backend service performance

---

## Success Criteria Summary

All tests must pass for production readiness:

- [x] **Test 1:** Backend health check shows all services connected
- [x] **Test 2:** Session creation returns unique UUID v4
- [x] **Test 3:** Frontend records audio from microphone
- [x] **Test 4:** Backend processes voice with valid session
- [x] **Test 5:** Audio URL serves valid MP3 file
- [x] **Test 6:** Browser plays Rose's voice automatically
- [x] **Test 7:** Multi-turn conversation maintains context

---

## Performance Benchmarks

### First Request (Cold Start)
- Session creation: < 500ms
- Microphone access: < 2s (includes user permission)
- Speech-to-text: 2-5s
- Workflow execution: 3-8s
- Text-to-speech: 2-5s
- **Total: 8-20s** (acceptable for cold start)

### Subsequent Requests (Warm)
- Speech-to-text: 1-3s
- Workflow execution: 1-3s
- Text-to-speech: 1-2s (may use cache)
- **Total: 3-8s** (optimal)

### Audio Playback
- Load time: < 2s
- Start delay: < 500ms (autoplay)

---

## Common Issues and Fixes

### "No voice output, but UI is clickable"
**Symptoms:** Interface responds to clicks, but no sound plays
**Root Cause:** Session ID not created before voice request
**Fix:** ✅ Fixed in this update - session created automatically on first tap

**Verify Fix:**
1. Check console logs for `🎫 Session created` BEFORE `🔴 Starting recording`
2. Check Network tab - `/api/v1/voice/process` should include `session_id` in form data
3. No 422 errors in Network tab

### "422 Unprocessable Entity"
**Symptoms:** Backend rejects voice request
**Root Cause:** Missing or invalid `session_id` in request
**Fix:**
1. Check console - should show session creation
2. Verify `session_id` is string UUID, not `undefined`
3. Check `processVoice()` call includes session_id parameter

### "Audio doesn't autoplay"
**Symptoms:** Response received but no sound
**Root Cause:** Browser autoplay policy
**Fix:**
1. User must interact with page first (tap/click) ✅ Already required
2. Check console for autoplay errors
3. Try different browser (Chrome recommended)

### "Recording doesn't start when speaking"
**Symptoms:** Microphone granted but no recording
**Root Cause:** VAD threshold too high for environment
**Fix:**
1. Press `Ctrl+Shift+D` to open dev panel
2. Lower `RMS_ACTIVATION_THRESHOLD` (try 0.005)
3. Increase `RMS_DEACTIVATION_THRESHOLD` (try 0.01)
4. Speak louder or closer to microphone

### "Rose doesn't remember previous conversation"
**Symptoms:** Each message treated as new conversation
**Root Cause:** Session ID not persisting between turns
**Fix:**
1. Check console - same `session_id` for all turns?
2. Verify `sessionId` state not reset after response
3. Check `setSessionId()` called in `startRecording()`

---

## Logging Reference

### Frontend Emojis
- 🎤 Voice session events
- 🎫 Session creation
- 🎙️ Microphone access
- 🔴 Recording start
- ⏹️ Recording stop
- 📦 Audio blob creation
- 📤 API requests
- ✅ Success events
- ❌ Errors
- 💬 Transcription
- 🔊 Audio playback
- ⏰ Timeouts
- ⏳ Retries

### Backend Emojis
- 🎤 Voice processing
- 🎫 Session management
- 📊 Metrics
- ✅ Success
- ❌ Errors
- 🏥 Health checks

---

## Developer Commands

### Build and Deploy Frontend
```bash
cd frontend
npm install
npm run build
rm -rf ../src/ai_companion/interfaces/web/static/assets
cp -r dist/* ../src/ai_companion/interfaces/web/static/
```

### Start Backend
```bash
uv run python -m ai_companion.interfaces.web.app
```

### Check Logs (JSON Format)
```bash
# Filter by event type
cat backend.log | grep "voice_processing_started"

# Filter by session ID
cat backend.log | grep "xxxxxxxx-xxxx-4xxx"

# Count errors
cat backend.log | grep "❌" | wc -l
```

### Test Individual Endpoints
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Create session
curl -X POST http://localhost:8000/api/v1/session/start

# Process voice (requires audio file)
curl -X POST http://localhost:8000/api/v1/voice/process \
  -F "audio=@test.webm" \
  -F "session_id=xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx"

# Get audio file
curl http://localhost:8000/api/v1/voice/audio/AUDIO_ID -o response.mp3
```

---

## Architecture Verification

This smoke test validates the complete architecture:

```
┌─────────────┐
│   Browser   │ 1. User taps screen
│  (Frontend) │ 2. Creates session (/session/start)
└──────┬──────┘ 3. Requests microphone
       │        4. Records speech via VAD
       │        5. Sends audio + session_id
       ▼
┌─────────────┐
│   FastAPI   │ 6. Validates session_id (Required!)
│  (Backend)  │ 7. Transcribes with Groq Whisper
└──────┬──────┘ 8. Processes with LangGraph + Claude
       │        9. Generates TTS with ElevenLabs
       │        10. Saves MP3, returns URL
       ▼
┌─────────────┐
│   Browser   │ 11. Fetches audio from URL
│  (Playback) │ 12. Plays Rose's voice
└─────────────┘ 13. Returns to listening (same session)
```

**Critical Fix Implemented:**
- ✅ Step 2 now happens BEFORE Step 3 (was missing before!)
- ✅ session_id is REQUIRED in Step 5 (was optional)
- ✅ Step 6 validates session_id (previously failed with 422)

---

## Sign-Off Checklist

Before marking voice system as production-ready:

- [ ] All 7 smoke tests passed
- [ ] Performance benchmarks met
- [ ] Console shows clean logging trail with emojis
- [ ] Zero 422 errors in Network tab
- [ ] Multi-turn conversation maintains context
- [ ] Session ID consistent across all requests
- [ ] Rose's voice plays clearly without distortion
- [ ] VAD accurately detects speech and silence
- [ ] Error handling tested (disconnect mic, network failure)
- [ ] Tested on target browsers (Chrome, Edge)
- [ ] Backend logs show complete request flow
- [ ] No magic numbers in code (all constants named)

---

**Last Updated:** 2025-11-12
**Version:** 1.0
**Tested By:** _____________
**Sign-Off Date:** _____________
