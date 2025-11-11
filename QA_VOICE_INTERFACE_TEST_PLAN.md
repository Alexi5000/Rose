# 🎙️ Rose Voice Interface - QA Test Plan

**Role:** Senior QA Tester
**Objective:** Verify 100% functionality of voice interface (listen & respond in voice)
**Date:** 2025-11-10
**Status:** 🔄 In Progress

---

## 🦆 Rubber Duck Analysis

### Architecture Overview
```
User Interaction Flow:
1. 🎤 User presses voice button (push-to-talk)
2. 📱 Browser captures audio via MediaRecorder API
3. 🌐 Frontend sends WebM blob to backend via /api/v1/voice/process
4. 🎙️ Backend transcribes audio (Groq Whisper)
5. 🧠 Backend processes through LangGraph workflow (Rose AI)
6. 🔊 Backend generates audio response (ElevenLabs TTS)
7. 📦 Backend saves MP3 and returns URL
8. 🔄 Frontend fetches and plays audio
9. ✅ User hears Rose's voice response
```

### Critical Components

| Component | Status | Risk Level |
|-----------|--------|------------|
| Docker Services (Qdrant, Rose) | ✅ Running | 🟢 Low |
| Backend Health | ✅ All services connected | 🟢 Low |
| Frontend Served | ✅ HTML loading | 🟢 Low |
| Microphone Access | ⚠️ Needs testing | 🟡 Medium |
| STT (Groq Whisper) | ⚠️ Needs API key verification | 🟡 Medium |
| TTS (ElevenLabs) | ⚠️ Needs API key verification | 🟡 Medium |
| Audio Playback | ⚠️ Needs testing | 🟡 Medium |

---

## 📋 Test Plan (Following YAGNI Principle)

### Phase 1: Backend API Testing (Automated) 🤖

#### Test 1.1: Health Check Endpoint
```bash
# Expected: All services "connected"
curl http://localhost:8000/api/v1/health
```

**Expected Result:**
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

**Success Criteria:** ✅ All services return "connected"
**Log Point:** 🏥 Backend health verified

---

#### Test 1.2: Session Creation
```bash
# Expected: Returns session_id (UUID v4)
curl -X POST http://localhost:8000/api/v1/session/start
```

**Expected Result:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Session started successfully"
}
```

**Success Criteria:** ✅ Returns valid UUID v4
**Log Point:** 🔑 Session ID created

---

#### Test 1.3: Voice Processing Endpoint (with test audio)
```bash
# Expected: Returns transcribed text + audio URL
curl -X POST http://localhost:8000/api/v1/voice/process \
  -F "audio=@test_audio.webm" \
  -F "session_id=YOUR_SESSION_ID"
```

**Expected Result:**
```json
{
  "text": "I hear you. Tell me more about how you're feeling.",
  "audio_url": "/api/v1/voice/audio/AUDIO_UUID",
  "session_id": "YOUR_SESSION_ID"
}
```

**Success Criteria:**
- ✅ Status 200
- ✅ Returns text response
- ✅ Returns audio_url path
- ✅ Audio file exists at URL

**Log Points:**
- 🎤 Audio received (size in bytes)
- 📝 Transcription complete
- 🧠 Workflow processed
- 🔊 TTS generated
- 💾 Audio file saved

---

### Phase 2: Frontend Manual Testing 👤

#### Test 2.1: Page Load & UI Rendering
**Steps:**
1. Open http://localhost:8000 in browser
2. Wait for 3D scene to load
3. Verify voice button appears

**Expected Result:**
- ✅ Page loads without errors
- ✅ 3D scene renders (igloo, water, aurora)
- ✅ Voice button visible at bottom center
- ✅ Button shows microphone-off icon (idle state)

**Success Criteria:** No console errors, button interactive
**Log Point:** 🎨 Frontend loaded successfully

---

#### Test 2.2: Microphone Permission Request
**Steps:**
1. Click voice button once
2. Browser requests microphone permission
3. Click "Allow"

**Expected Result:**
- ✅ Browser shows permission prompt
- ✅ Permission granted
- ✅ No errors in console

**Success Criteria:** Microphone access granted
**Log Point:** 🎤 Microphone permission granted

**Fallback (if denied):**
- ❌ Error message shown to user
- 🔴 Button shows error state

---

#### Test 2.3: Audio Recording (Push-to-Talk)
**Steps:**
1. Press and HOLD voice button
2. Speak clearly: "Hello Rose, I'm feeling sad today"
3. Release button after 3-5 seconds

**Expected Result:**
- ✅ Button changes to "listening" state (blue glow, ripple effect)
- ✅ Audio visualization shows waveform
- ✅ On release, button changes to "processing" state (spinning loader)

**Success Criteria:**
- Recording starts on press
- Recording stops on release
- Visual feedback matches state

**Log Points:**
- 🎙️ Recording started
- 📊 Audio blob size (bytes)
- 📤 Sending to backend

---

#### Test 2.4: Backend Processing
**Steps:**
1. Wait for backend to process
2. Monitor console logs
3. Verify no errors

**Expected Result:**
- ✅ Console shows: "📤 API Request: POST /voice/process"
- ✅ Console shows: "✅ API Response: 200"
- ✅ Response contains text + audio_url
- ✅ Button changes to "speaking" state (orange glow, pulsing)

**Success Criteria:** Backend returns successfully
**Log Points:**
- 🎙️ Transcription: "[transcribed text]"
- 🧠 Workflow response: "[Rose's response]"
- 🔊 TTS audio URL received

---

#### Test 2.5: Audio Playback
**Steps:**
1. Wait for audio to load
2. Audio automatically plays (Rose's voice)
3. Wait for playback to complete

**Expected Result:**
- ✅ Audio loads without errors
- ✅ Rose's voice plays clearly
- ✅ Audio volume is appropriate
- ✅ Button pulses during playback
- ✅ Button returns to idle after playback

**Success Criteria:**
- Audio plays without stutter
- Voice is clear and warm
- Button returns to idle when done

**Log Points:**
- 🔊 Audio loading...
- ▶️ Audio playing
- ✅ Playback complete

**Fallback (if autoplay blocked):**
- ⚠️ User sees "Click to play" message
- 🔄 Manual play button appears

---

### Phase 3: Error Handling Tests 🚨

#### Test 3.1: No Internet Connection
**Steps:**
1. Disconnect internet
2. Try to use voice button

**Expected Result:**
- ❌ Error: "No internet connection. Please check your network."
- 🔴 Button shows error state

**Log Point:** ❌ Network error detected

---

#### Test 3.2: Backend Unreachable
**Steps:**
1. Stop Docker container: `docker-compose down`
2. Try to use voice button

**Expected Result:**
- ❌ Error: "Unable to reach server. Please try again."
- 🔴 Button shows error state

**Log Point:** ❌ Backend unreachable

---

#### Test 3.3: Audio Too Short (< 0.1 seconds)
**Steps:**
1. Press and immediately release button (< 100ms)

**Expected Result:**
- ⚠️ No API call made (audio discarded as too short)
- 🔵 Button returns to idle
- 💬 Optional toast: "Recording too short, please try again"

**Log Point:** ⚠️ Utterance discarded (too small)

---

#### Test 3.4: Rate Limiting
**Steps:**
1. Send 11+ requests within 1 minute

**Expected Result:**
- ❌ Error: "Too many requests. Please wait a moment."
- 🔴 Button disabled temporarily
- ⏱️ Cooldown period shown

**Log Point:** ⚠️ Rate limit reached

---

### Phase 4: Cross-Browser Testing 🌐

#### Browsers to Test
| Browser | Version | WebRTC Support | Priority |
|---------|---------|----------------|----------|
| Chrome | Latest | ✅ Excellent | 🔴 High |
| Edge | Latest | ✅ Excellent | 🔴 High |
| Firefox | Latest | ✅ Good | 🟡 Medium |
| Safari | Latest | ⚠️ Limited | 🟢 Low |

**Test Matrix:**
- ✅ Microphone access
- ✅ Audio recording (MediaRecorder)
- ✅ WebM format support
- ✅ Audio playback (MP3)
- ✅ Autoplay policies

---

## 🎯 Success Metrics (Uncle Bob Approved)

### Must-Pass Criteria (100% Required)
1. ✅ Backend health check passes
2. ✅ Session creation works
3. ✅ Voice button renders and is interactive
4. ✅ Microphone permission can be granted
5. ✅ Audio recording captures voice
6. ✅ Backend successfully transcribes audio
7. ✅ Backend returns text response
8. ✅ Backend generates TTS audio
9. ✅ Frontend plays audio response
10. ✅ Complete round-trip < 10 seconds

### Quality Metrics
- ⚡ End-to-end latency: < 8 seconds (95th percentile)
- 🔊 Audio quality: Clear, no distortion
- 🎤 Transcription accuracy: > 95% for clear speech
- 💬 Response relevance: Contextually appropriate
- 🔄 UI responsiveness: Smooth state transitions

---

## 🚫 Anti-Patterns to Avoid (Uncle Bob)

### ❌ Magic Numbers
- All timeouts, limits, and thresholds must be named constants
- Example: `AUDIO_TIMEOUT_MS = 60000` ✅ not `60000` ❌

### ❌ Missing Logs
- Every critical decision point must have emoji-tagged logs
- Example: `console.log('🎤 Recording started', { duration, size })` ✅

### ❌ Silent Failures
- All errors must be surfaced to user with actionable messages
- Example: "Microphone blocked. Click here to enable." ✅

### ❌ Unverified Assumptions
- Test all happy paths AND failure modes
- Don't assume API keys are valid - verify!

---

## 📊 Test Execution Checklist

### Pre-Flight Checks ✈️
- [ ] Docker services running (`docker-compose ps`)
- [ ] Backend health check passes
- [ ] `.env` file has valid API keys
- [ ] Frontend loads without errors
- [ ] Browser console clear of errors

### Automated Tests 🤖
- [ ] Health check endpoint
- [ ] Session creation endpoint
- [ ] Voice processing with test audio file
- [ ] Audio serving endpoint
- [ ] Error responses (400, 413, 429, 500)

### Manual Tests 👤
- [ ] Page load & rendering
- [ ] Microphone permission flow
- [ ] Audio recording (push-to-talk)
- [ ] Backend processing
- [ ] Audio playback
- [ ] Error handling (network, rate limit, etc.)

### Cross-Browser Tests 🌐
- [ ] Chrome (latest)
- [ ] Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest) - optional

---

## 🐛 Known Issues & Gotchas

### Issue 1: Autoplay Blocked
**Symptoms:** Audio doesn't play automatically
**Cause:** Browser autoplay policy requires user interaction
**Solution:** Frontend shows "Click to play" button
**Status:** ✅ Handled gracefully

### Issue 2: Microphone Permission Denied
**Symptoms:** Recording fails silently
**Cause:** User denied microphone access
**Solution:** Clear error message + instructions
**Status:** ⚠️ Needs verification

### Issue 3: CORS on Audio Files
**Symptoms:** Audio fails to load from external URLs
**Cause:** Missing `crossOrigin` attribute
**Solution:** Conditional crossOrigin based on domain
**Status:** ✅ Implemented (line 171-178 of useVoicePipeline.ts)

---

## 🔧 Test Automation Script

```python
# scripts/test_voice_pipeline.py
"""
Automated test for voice pipeline end-to-end
Uncle Bob approved: No magic numbers, comprehensive logging
"""

import requests
import time
from pathlib import Path

# Constants (No Magic Numbers!)
BACKEND_URL = "http://localhost:8000"
HEALTH_ENDPOINT = f"{BACKEND_URL}/api/v1/health"
SESSION_ENDPOINT = f"{BACKEND_URL}/api/v1/session/start"
VOICE_ENDPOINT = f"{BACKEND_URL}/api/v1/voice/process"
TEST_AUDIO_PATH = Path("tests/fixtures/test_recording.webm")
EXPECTED_RESPONSE_TIME_SECONDS = 10
HTTP_STATUS_OK = 200

def test_voice_pipeline():
    """Test complete voice pipeline from audio upload to response"""

    print("🏥 Testing backend health...")
    health = requests.get(HEALTH_ENDPOINT)
    assert health.status_code == HTTP_STATUS_OK
    assert health.json()["status"] == "healthy"
    print("✅ Backend healthy")

    print("🔑 Creating session...")
    session = requests.post(SESSION_ENDPOINT)
    assert session.status_code == HTTP_STATUS_OK
    session_id = session.json()["session_id"]
    print(f"✅ Session created: {session_id}")

    print("🎤 Processing voice input...")
    start_time = time.time()

    with open(TEST_AUDIO_PATH, 'rb') as audio_file:
        files = {'audio': audio_file}
        data = {'session_id': session_id}
        response = requests.post(VOICE_ENDPOINT, files=files, data=data)

    duration = time.time() - start_time

    assert response.status_code == HTTP_STATUS_OK
    result = response.json()

    print(f"✅ Voice processed in {duration:.2f}s")
    print(f"📝 Transcribed text: {result['text']}")
    print(f"🔊 Audio URL: {result['audio_url']}")

    # Verify audio file exists
    audio_url = f"{BACKEND_URL}{result['audio_url']}"
    audio_check = requests.head(audio_url)
    assert audio_check.status_code == HTTP_STATUS_OK
    print(f"✅ Audio file accessible")

    # Performance check
    if duration > EXPECTED_RESPONSE_TIME_SECONDS:
        print(f"⚠️ Response time {duration:.2f}s exceeds target {EXPECTED_RESPONSE_TIME_SECONDS}s")
    else:
        print(f"⚡ Response time within target")

    print("🎉 All tests passed!")

if __name__ == "__main__":
    test_voice_pipeline()
```

---

## 🎓 Testing Best Practices (Senior QA)

### 1. Test in Isolation First
- ✅ Test each component independently before integration
- ✅ Use mock data to isolate frontend from backend issues

### 2. Test the Happy Path First
- ✅ Verify core functionality works before edge cases
- ✅ Build confidence with working flow first

### 3. Then Test Failure Modes
- ✅ Network errors, timeouts, invalid input
- ✅ Graceful degradation, not crashes

### 4. Verify Logs at Every Step
- ✅ Ensure logs exist at critical decision points
- ✅ Logs should be searchable with emoji prefixes

### 5. Document Everything
- ✅ Record steps, expected results, actual results
- ✅ Screenshots/videos for visual issues
- ✅ Browser console logs for debugging

---

## 🚀 Next Steps

### Immediate Actions
1. ✅ Verify API keys in `.env` are valid
2. ✅ Run automated backend tests
3. ✅ Open frontend in browser and test manually
4. ✅ Record findings in this document

### If Tests Fail
1. 🔍 Check logs (emoji prefixes make them easy to search)
2. 🐛 Isolate the failing component
3. 🔧 Fix the root cause (not symptoms!)
4. ♻️ Re-test end-to-end

### Once Tests Pass
1. 📹 Record a demo video showing the complete flow
2. 📊 Benchmark performance (latency, audio quality)
3. 🌐 Test on other browsers
4. 📚 Update documentation with any findings

---

**Generated with:** Claude Code (Sonnet 4.5)
**Date:** 2025-11-10
**Status:** 🎯 Ready for testing
**YAGNI Approved:** ✅ Simple, focused, no unnecessary complexity
