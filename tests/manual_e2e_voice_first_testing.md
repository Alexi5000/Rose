# Manual End-to-End Testing Guide: Voice-First Consistency

## Overview
This guide provides step-by-step instructions for manually testing the voice-first consistency feature across all input types in the Chainlit interface.

## Prerequisites
- Chainlit application running locally
- Browser with audio playback enabled
- Valid API keys configured in `.env`:
  - `GROQ_API_KEY`
  - `ELEVENLABS_API_KEY`
  - `ELEVENLABS_VOICE_ID` or `ROSE_VOICE_ID`

## Test Environment Setup

### 1. Start Chainlit Application
```bash
# From project root
uv run chainlit run src/ai_companion/interfaces/chainlit/app.py
```

### 2. Open Browser
- Navigate to `http://localhost:8000`
- Open browser developer console (F12)
- Ensure audio is not muted

## Test Cases

### Test 1: 10 Consecutive Text Messages with Voice
**Requirement: 1.1, 3.4**

**Steps:**
1. Send the following text messages one by one:
   - "Hello Rose"
   - "How are you today?"
   - "Tell me about healing"
   - "What is mindfulness?"
   - "Can you help me relax?"
   - "I'm feeling stressed"
   - "Tell me a calming story"
   - "What should I focus on?"
   - "How can I be more present?"
   - "Thank you for your help"

**Expected Results:**
- ✅ Each response includes audio element with "Rose's Voice"
- ✅ Audio auto-plays for each response
- ✅ No console errors
- ✅ Text content is displayed alongside audio

**Verification Checklist:**
- [ ] All 10 responses have audio elements
- [ ] Audio auto-plays without manual interaction
- [ ] No JavaScript errors in console
- [ ] Audio quality is clear and consistent

---

### Test 2: 10 Consecutive Voice Messages with Voice
**Requirement: 1.2, 3.4**

**Steps:**
1. Click the microphone icon to start recording
2. Speak the following messages (one at a time):
   - "Hello Rose"
   - "How are you?"
   - "Tell me about meditation"
   - "What is breathing exercise?"
   - "Can you guide me?"
   - "I need help"
   - "Tell me something calming"
   - "What should I do?"
   - "How can I improve?"
   - "Thank you"

**Expected Results:**
- ✅ Each response includes audio element with "Rose's Voice"
- ✅ Audio auto-plays for each response
- ✅ Transcription is accurate
- ✅ No console errors

**Verification Checklist:**
- [ ] All 10 responses have audio elements
- [ ] Audio auto-plays without manual interaction
- [ ] Voice transcription is accurate
- [ ] No JavaScript errors in console

---

### Test 3: Mixed Text and Voice Messages
**Requirement: 1.1, 1.2, 3.4**

**Steps:**
1. Send text: "Hello Rose"
2. Send voice: "How are you?"
3. Send text: "Tell me about healing"
4. Send voice: "What is mindfulness?"
5. Send text: "Can you help me?"
6. Send voice: "I'm feeling stressed"
7. Send text: "Tell me a story"
8. Send voice: "What should I focus on?"
9. Send text: "How can I be present?"
10. Send voice: "Thank you"

**Expected Results:**
- ✅ All responses have audio regardless of input type
- ✅ Audio auto-plays consistently
- ✅ No difference in behavior between text and voice inputs
- ✅ No console errors

**Verification Checklist:**
- [ ] All 10 responses have audio elements
- [ ] No difference in audio behavior between input types
- [ ] Audio auto-plays for both text and voice inputs
- [ ] No JavaScript errors in console

---

### Test 4: Image with Text and Voice Response
**Requirement: 1.3, 1.4**

**Steps:**
1. Click the attachment icon
2. Upload an image (any image file)
3. Add text: "What do you see in this image?"
4. Send the message

**Expected Results:**
- ✅ Response includes both image and audio elements
- ✅ Audio auto-plays
- ✅ Image is displayed inline
- ✅ Rose describes the image with voice

**Verification Checklist:**
- [ ] Response has audio element
- [ ] Response has image element
- [ ] Audio auto-plays
- [ ] Image description is relevant
- [ ] No console errors

---

### Test 5: TTS Failure Graceful Degradation
**Requirement: 1.5, 3.1, 3.2, 3.3**

**Note:** This test requires simulating a failure condition. Options:
- Temporarily set invalid `ELEVENLABS_API_KEY`
- Disconnect network during message
- Use network throttling in browser dev tools

**Steps:**
1. Simulate TTS failure condition
2. Send text message: "Hello Rose"
3. Observe response

**Expected Results:**
- ✅ Text response is displayed
- ✅ No audio element (graceful degradation)
- ✅ No user-facing error message
- ✅ Error logged in server console

**Verification Checklist:**
- [ ] Text response received
- [ ] No audio element present
- [ ] No error message shown to user
- [ ] Error logged in server logs

---

### Test 6: Audio Auto-Play Verification
**Requirement: 1.4**

**Steps:**
1. Send text message: "Hello Rose"
2. Observe audio element behavior
3. Check audio element properties in browser inspector

**Expected Results:**
- ✅ Audio starts playing automatically
- ✅ Audio element has `autoplay` attribute
- ✅ No manual play button click required

**Verification Checklist:**
- [ ] Audio plays without user interaction
- [ ] Audio element has autoplay enabled
- [ ] Audio controls are visible
- [ ] Audio can be paused/replayed manually

---

### Test 7: Browser Console Error Check
**Requirement: All**

**Steps:**
1. Keep browser console open during all tests
2. Monitor for any errors or warnings
3. Check for:
   - JavaScript errors
   - Network errors
   - Audio playback errors
   - CORS errors

**Expected Results:**
- ✅ No JavaScript errors
- ✅ No network errors (except during failure test)
- ✅ No audio playback errors
- ✅ No CORS errors

**Verification Checklist:**
- [ ] No red errors in console
- [ ] No yellow warnings (except expected)
- [ ] Network tab shows successful API calls
- [ ] Audio elements load successfully

---

### Test 8: Server Log Review
**Requirement: 4.1, 4.2, 4.3, 4.4, 4.5**

**Steps:**
1. Review server logs during testing
2. Look for TTS-related log entries
3. Verify log structure and content

**Expected Log Entries:**
- ✅ "TTS generation successful" with metrics
- ✅ Thread ID in all log messages
- ✅ Duration, text length, audio size metrics
- ✅ Circuit breaker state changes (if any)
- ✅ Error logs with full context (during failure test)

**Verification Checklist:**
- [ ] Success logs include duration, text_length, audio_size
- [ ] All logs include thread_id
- [ ] Error logs include error_type and error message
- [ ] Circuit breaker state logged when not CLOSED
- [ ] No missing or malformed log entries

---

## Test Results Summary

### Overall Results
- [ ] All text messages generate voice responses
- [ ] All voice messages generate voice responses
- [ ] All image messages generate voice responses
- [ ] Audio auto-plays consistently
- [ ] TTS failures degrade gracefully
- [ ] No user-facing errors
- [ ] Comprehensive logging present

### Issues Found
(Document any issues discovered during testing)

---

### Performance Metrics
(Record observed performance)

- Average TTS generation time: _____ ms
- Longest TTS generation time: _____ ms
- TTS success rate: _____ %
- Audio quality: _____ (1-5 scale)

---

## Post-Testing Cleanup

1. Stop Chainlit application (Ctrl+C)
2. Review logs for any unexpected errors
3. Document any issues or improvements needed
4. Update task status in `.kiro/specs/voice-first-consistency/tasks.md`

---

## Notes
- Test in multiple browsers if possible (Chrome, Firefox, Safari)
- Test with different network conditions
- Test with different audio output devices
- Document any browser-specific issues
