# Debug Voice Interaction Issues

Diagnose and troubleshoot voice button and audio processing problems.

## Diagnostic Steps

### 1. Check User Interaction Pattern

**Most common issue**: Not using "press and hold" pattern correctly.

Display to user:
```
🎤 How to Use Voice Button (Like a Walkie-Talkie)

✅ CORRECT Way:
1. Press and HOLD Space bar (or mouse button)
2. Speak while holding
3. Release to send

❌ WRONG Way:
- Clicking once and waiting
- This makes button stay in "listening" forever!

Try this quick test:
1. Open http://localhost:8000
2. Press and HOLD Space
3. Say "Hello Rose"
4. Release Space
5. Wait for response (5-10 seconds)
```

### 2. Check Browser Console

Ask user to open Developer Tools (F12) and look for:

**Expected Messages:**
```
✅ 🔌 Initializing API client with base URL: /api/v1
✅ 🎤 Processing voice input...
✅ 📤 API Request: POST /voice/process
✅ ✅ API Response: /voice/process Status: 200
✅ 🔊 Playing audio response...
```

**Error Patterns:**
```
❌ "Microphone permission denied" → Need to allow mic
❌ "Cannot connect to backend" → Backend not running
❌ "Network error" → Check Docker containers
❌ "CORS error" → CORS misconfiguration
```

### 3. Check Microphone Permission

```javascript
// User should check:
// 1. Click padlock icon in address bar
// 2. Ensure "Microphone" is set to "Allow"
// 3. Refresh page after changing
```

### 4. Verify Backend is Processing

```bash
# Watch logs in real-time for voice events
docker-compose logs -f rose | grep -E "(🎤|voice|🔊|audio)"

# Expected logs when voice button used:
# - 🎤 voice_processing_started
# - groq_stt (speech-to-text)
# - workflow_execution_success
# - elevenlabs_tts (text-to-speech)
# - 🔊 audio playback
# - ✅ voice_processing_complete
```

### 5. Test API Endpoint Directly

```bash
# 1. Create session
SESSION=$(curl -s -X POST http://localhost:8000/api/v1/session/start | jq -r '.session_id')
echo "Session ID: $SESSION"

# 2. Check if voice endpoint is accessible
curl -I http://localhost:8000/api/v1/voice/process

# Should return: 405 Method Not Allowed (needs POST with audio)
# This confirms endpoint exists

# 3. Check API docs
curl http://localhost:8000/api/v1/docs
# Should load Swagger UI
```

### 6. Check Network Tab

Ask user to check Network tab in DevTools:

**What to look for:**
```
Request: POST /api/v1/voice/process
Status: Should be 200 OK
Type: Should be multipart/form-data
Size: Should show audio file upload

If request is RED/failed:
- Click on it
- Check "Response" tab for error message
- Share error details
```

### 7. Check Audio Playback

```bash
# Test if audio serving works
# (After a successful voice interaction)

# Check temp audio directory
docker exec rose-rose-1 ls -la /tmp/rose_audio/

# Should see .mp3 files
# Example: abc123-def456.mp3
```

### 8. Check API Keys

```bash
# Verify API keys are set (without showing values)
docker exec rose-rose-1 env | grep -E "(GROQ|ELEVENLABS)" | sed 's/=.*/=***CONFIGURED***/'

# Expected:
# GROQ_API_KEY=***CONFIGURED***
# ELEVENLABS_API_KEY=***CONFIGURED***
# ELEVENLABS_VOICE_ID=***CONFIGURED***

# If missing, check .env file
```

## Common Issues and Fixes

### Issue 1: "Button stays on listening forever"
**Cause**: Not releasing Space/mouse button
**Fix**:
```
User must:
1. HOLD Space bar
2. Speak
3. RELEASE Space bar <-- This is critical!
```

### Issue 2: "No microphone permission"
**Cause**: Browser hasn't granted mic access
**Fix**:
```
1. Click padlock in address bar
2. Change Microphone to "Allow"
3. Refresh page (Ctrl+R)
```

### Issue 3: "Backend unreachable"
**Cause**: Docker container not running
**Fix**:
```bash
docker-compose ps
# If not running:
docker-compose up -d
```

### Issue 4: "Processing but no response"
**Possible Causes**:
1. Groq API key invalid → Check logs for "401 Unauthorized"
2. ElevenLabs key invalid → Check logs for TTS errors
3. Network timeout → Check logs for "timeout" errors

**Debug**:
```bash
# Check recent errors
docker-compose logs rose --tail 100 | grep -E "(❌|ERROR|error|failed)"

# Test Groq API key
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY"

# Should return list of models
```

### Issue 5: "No audio plays back"
**Possible Causes**:
1. Browser volume muted
2. System volume muted
3. Audio element error
4. CORS blocking audio file

**Debug**:
```javascript
// In browser console:
const audio = new Audio('http://localhost:8000/api/v1/voice/audio/test-id');
audio.play().catch(e => console.error('Audio error:', e));
```

### Issue 6: "CORS errors"
**Cause**: Frontend on different origin than backend
**Fix**:
```python
# Check CORS settings in src/ai_companion/settings.py
# Should include frontend origin in ALLOWED_ORIGINS
```

## Debugging Checklist

Run through this checklist:

```
□ User understands "press and hold" pattern
□ Microphone permission granted in browser
□ Backend container is running (docker-compose ps)
□ Health check passes (/api/v1/health)
□ API keys configured (GROQ, ELEVENLABS)
□ No errors in recent logs
□ Frontend loads successfully
□ Network tab shows /voice/process request
□ Browser console shows no errors
□ Audio playback not muted
```

## Output Format

Provide diagnostic summary:

```markdown
# 🔍 Voice Interaction Diagnostic Report

## User Interaction
- [ ] Understands press-and-hold pattern
- [ ] Microphone permission granted
- [ ] Browser: Chrome/Edge/Firefox

## Backend Status
- [ ] Container running
- [ ] Health check: ✅ Healthy
- [ ] API keys: ✅ Configured
- [ ] Recent errors: None

## Frontend Status
- [ ] Loads successfully
- [ ] Console errors: None
- [ ] Network requests: Working

## Issue Identified
[Describe the specific issue found]

## Recommended Fix
[Provide step-by-step fix]

## Follow-up Actions
1. [Action items for user]
2. [Testing steps]
3. [Verification]
```
