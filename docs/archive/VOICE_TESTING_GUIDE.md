# 🎤 Rose Voice Testing Guide

## ✅ How to Use the Voice Button

### The voice button works like a walkie-talkie:
- **Hold to talk, release to send**

### Three Ways to Talk to Rose:

#### 1. 🖱️ Mouse Method
```
1. Click and HOLD the microphone button
2. Speak while holding the mouse button down
3. Release the mouse button when done speaking
4. Rose will process and respond
```

#### 2. ⌨️ Keyboard Method (Easiest!)
```
1. Press and HOLD Space bar (or Enter key)
2. Speak while holding the key down
3. Release the key when done speaking
4. Rose will process and respond
```

#### 3. 🚫 Cancel Recording
```
Press Escape key to cancel recording
```

## 🎯 Quick Test (30 seconds)

1. Open http://localhost:8000
2. **Press and HOLD Space bar**
3. Say: "Hello Rose, I'm feeling sad today"
4. **Release Space bar**
5. Wait for Rose's response (should take 5-10 seconds)

## 📊 What You Should See

### Visual Feedback:
1. **Idle**: Button is calm and neutral
2. **Listening** (while holding): Button pulses with green glow
3. **Processing**: Button shows "Processing your message..."
4. **Speaking**: Button pulses with orange glow while Rose talks

### Console Messages (F12):
```
🎤 Processing voice input...
📤 API Request: POST /voice/process
✅ API Response: /voice/process Status: 200
✅ Voice processing successful
🔊 Playing audio response...
✅ Audio playback started
✅ Audio playback completed
```

## 🐛 Troubleshooting

### Issue: "It stays on listening forever"
**Cause**: You're not releasing the button/key
**Fix**: Make sure to **release** the Space key or mouse button

### Issue: "Nothing happens when I press"
**Cause**: Microphone permission denied
**Fix**:
1. Click padlock icon in address bar
2. Allow microphone
3. Refresh page

### Issue: "I get an error message"
Check browser console (F12) for specific error and share it with me.

### Issue: "No sound plays back"
**Check**:
1. Browser volume not muted
2. System volume not muted
3. Check console for playback errors

## 🧪 API Test (If Voice Button Still Doesn't Work)

If the voice button doesn't work after following the steps above, let's test the API directly:

### Step 1: Create a test session
```bash
curl -X POST http://localhost:8000/api/v1/session/start
```

You should see:
```json
{"session_id":"xxx-xxx-xxx","message":"Session initialized..."}
```

### Step 2: Check if voice endpoint responds
```bash
curl http://localhost:8000/api/v1/docs
```

This opens the API docs where you can test the `/api/v1/voice/process` endpoint directly.

## 📸 What to Share If It Still Doesn't Work

1. Screenshot of browser console (F12 → Console tab) showing any errors
2. Screenshot of Network tab (F12 → Network) after trying to record
3. Tell me:
   - Did you hold and release the button/key?
   - Did it ask for microphone permission?
   - What state did the button stay in? (idle/listening/processing/speaking)
   - Any error messages visible on screen?

## 🎉 Expected Result

When working correctly:
1. Hold Space → Button turns green and pulses → "Listening..."
2. Release Space → Button shows "Processing your message..."
3. After 5-10 seconds → Rose's voice response plays
4. Button returns to idle state

**Total time from speaking to hearing response: 5-15 seconds**

---

## 🚨 Most Common Mistake

❌ **Clicking once and waiting**
- The button will stay in "listening" mode forever because you didn't release it!

✅ **Correct way: Hold → Speak → Release**
- Like a walkie-talkie or voice memo button on your phone
