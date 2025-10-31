# 🎤 Voice Button Diagnostic Test

## Step 1: Open Browser Console
1. Open http://localhost:8000 in Chrome/Edge
2. Press F12 to open Developer Tools
3. Go to "Console" tab
4. Clear all messages

## Step 2: Check Initial State
Look for these console messages when page loads:
```
🔌 Initializing API client with base URL: /api/v1
```

If you DON'T see this, the frontend JavaScript isn't loading correctly.

## Step 3: Test Voice Button
1. Click the voice button (or press Space/Enter)
2. Watch the console for messages

**Expected Console Messages:**
```
🎤 Processing voice input...
📤 API Request: POST /voice/process
✅ API Response: /voice/process Status: 200
✅ Voice processing successful
🔊 Playing audio response...
✅ Audio playback started
✅ Audio playback completed
```

## Step 4: Check Network Tab
1. Go to "Network" tab in Developer Tools
2. Try voice button again
3. Look for request to `/api/v1/voice/process`

**What to check:**
- ❓ Does the request appear?
- ❓ What's the status code? (Should be 200)
- ❓ If it's red/failed, what's the error?
- ❓ Click on the request → "Preview" tab → what's the response?

## Step 5: Check Microphone Permission
1. Click the padlock icon in address bar (left of URL)
2. Check if "Microphone" permission is "Allow"
3. If blocked, change to "Allow" and refresh page

## Step 6: Test from Command Line

Open a command prompt and run:

```bash
# 1. Start a session
curl -X POST http://localhost:8000/api/v1/session/start

# You'll get back something like:
# {"session_id":"b29a0d9f-dca8-4ac7-9fc7-8cfbe5b23478","message":"..."}

# 2. Test voice endpoint with a small test file
# (We need to create a test audio file for this)
```

## Common Issues and Fixes

### Issue 1: Microphone Permission Denied
**Symptoms**: Button doesn't respond, no "listening" state
**Fix**:
1. Click padlock in address bar
2. Allow microphone
3. Refresh page

### Issue 2: HTTPS Required
**Symptoms**: Browser won't allow microphone access
**Explanation**: Modern browsers require HTTPS for microphone access (except localhost)
**Fix**: Since you're on localhost, this shouldn't be an issue

### Issue 3: Recording Never Stops
**Symptoms**: Button stays in "listening" state forever
**Possible Cause**:
- Not releasing the Space/Enter key (press and hold to record, release to send)
- Browser compatibility issue with MediaRecorder

### Issue 4: API Call Fails
**Symptoms**: Console shows `❌ API Error`
**Check**:
1. Network tab shows request with error status
2. Check backend logs: `docker-compose logs rose --tail 50`

### Issue 5: Audio Playback Fails
**Symptoms**: Processing completes but no sound
**Check**:
1. Browser volume not muted
2. System volume not muted
3. Check for CORS errors in console

## 📊 Share These Results

Please run through these steps and share:
1. Any ❌ error messages from console
2. Network tab status codes
3. Whether microphone permission was granted
4. Screenshots if helpful

This will help me identify the exact issue!
