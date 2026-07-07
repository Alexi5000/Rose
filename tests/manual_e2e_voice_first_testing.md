# Manual End-to-End Testing Guide: Voice-First Web App

## Overview

Use this guide to manually test the current Rose voice experience through the
React and FastAPI web app. This guide is for the active WebSocket and HTTP voice
paths, not the archived Chainlit, WhatsApp, or image-generation course flows.

## Prerequisites

- Python dependencies installed with `uv sync`
- Frontend dependencies installed with `cd frontend && npm install`
- Browser with microphone and audio playback enabled
- Valid provider configuration in `.env`:
  - `GROQ_API_KEY`
  - `ELEVENLABS_API_KEY`
  - `ELEVENLABS_VOICE_ID` or `ROSE_VOICE_ID`
  - `QDRANT_URL`
  - `QDRANT_API_KEY` when using Qdrant Cloud

Optional low-latency STT:

- `STT_PROVIDER=deepgram`
- `DEEPGRAM_API_KEY`
- `uv sync --extra streaming-stt`

## Test Environment Setup

### 1. Start Rose In Development Mode

```bash
python scripts/run_dev_server.py
```

Expected local services:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/api/v1/docs

### 2. Open Browser Tooling

- Navigate to http://localhost:3000.
- Grant microphone permission.
- Open browser developer tools.
- Keep the Console and Network tabs visible.
- Confirm the WebSocket connects to `/api/v1/voice/ws?session_id=...`.

## Test Cases

### Test 1: Session Start And Safety Boundary

**Steps:**

1. Load http://localhost:3000.
2. Confirm the app creates or restores a session.
3. Read the visible product boundary before speaking.

**Expected Results:**

- [ ] The page loads without red console errors.
- [ ] The UI identifies Rose as AI emotional support, not clinical care.
- [ ] A session ID is created or restored in browser storage.
- [ ] The backend health endpoint responds at `/api/v1/health`.

---

### Test 2: Ten Consecutive Voice Turns

**Steps:**

1. Tap to start the voice session.
2. Speak the following messages one at a time:
   - "Hello Rose."
   - "How are you today?"
   - "Help me slow down for a minute."
   - "I feel tense in my shoulders."
   - "Can you guide a short breath?"
   - "What should I notice right now?"
   - "I am feeling a little lonely."
   - "Tell me something grounding."
   - "What can I do after this call?"
   - "Thank you."

**Expected Results:**

- [ ] Rose responds with audio for every turn unless a tested fallback is active.
- [ ] Transcript snippets appear for user speech and Rose responses.
- [ ] Audio starts promptly and plays through without clipping.
- [ ] The voice state returns to listening after each response.
- [ ] No raw transcript text appears in server error logs when `LOG_SENSITIVE_CONTENT=false`.

---

### Test 3: WebSocket Streaming And Timing Metadata

**Steps:**

1. Keep the Network tab open.
2. Complete one normal voice turn.
3. Inspect WebSocket messages.
4. Open http://localhost:8000/api/v1/metrics.

**Expected Results:**

- [ ] Client sends `start_listening`, binary audio, then `stop_listening`.
- [ ] Server sends `transcription`, `response` or `response_delta`, `audio_start`, binary audio, and `audio_end`.
- [ ] The final `audio_end` message includes `timings`.
- [ ] Metrics include voice timing histograms such as `ws_voice_mic_to_first_audio_ms` and `ws_voice_turn_total_ms`.

---

### Test 4: Interruption And Barge-In

**Steps:**

1. Ask Rose for a longer grounding reflection.
2. While Rose is speaking, tap or speak to interrupt.
3. Ask a short follow-up: "Actually, just give me one breath."

**Expected Results:**

- [ ] Current playback stops or fades quickly.
- [ ] The client sends an `interrupt` control message when WebSocket is connected.
- [ ] Rose handles the follow-up as the next turn rather than continuing the old response.
- [ ] No overlapping audio continues after interruption.

---

### Test 5: Incomplete Turn Recovery

**Steps:**

1. Start speaking and intentionally stop mid-thought, such as: "What I really wanted to say was..."
2. Wait for Rose's response.

**Expected Results:**

- [ ] Rose asks for continuation instead of inventing the missing thought.
- [ ] WebSocket sends `turn_incomplete` when the backend detects a dangling fragment.
- [ ] Metrics increment `ws_voice_turn_incomplete_total`.
- [ ] The conversation remains warm and natural.

---

### Test 6: Memory Controls

**Steps:**

1. Turn on session-only memory in the UI.
2. Speak one emotionally specific but non-secret preference, such as: "I like very short grounding prompts."
3. Export session memories.
4. Use the forget control.

**Expected Results:**

- [ ] Session-only mode disables long-term memory for the session.
- [ ] Export returns sanitized memory records without embedding vectors.
- [ ] Forget deletes memories tagged to the session or reports that deletion could not be confirmed.
- [ ] No raw audio files are retained beyond processing.

API spot checks:

```bash
curl "http://localhost:8000/api/v1/session/$SESSION_ID/memory-preferences"
curl "http://localhost:8000/api/v1/session/$SESSION_ID/memory/export"
curl -X POST "http://localhost:8000/api/v1/session/$SESSION_ID/memory/forget"
```

---

### Test 7: Crisis Safety Routing

**Use synthetic test phrasing only. Do not run this with a person in active crisis.**

**Steps:**

1. Speak a direct self-harm test phrase.
2. Observe Rose's response.
3. Speak a non-crisis false-positive phrase such as: "This deadline is killing me, but I am safe."

**Expected Results:**

- [ ] Direct crisis language routes to the deterministic safety response.
- [ ] U.S. crisis copy includes 988 and encourages immediate human help.
- [ ] Rose does not provide therapy, diagnosis, or emergency-care claims.
- [ ] False-positive phrasing recovers into a normal supportive response.

---

### Test 8: TTS Failure Graceful Degradation

**Steps:**

1. Temporarily use an invalid `ELEVENLABS_API_KEY`, or block the TTS request in dev tools.
2. Restart the backend if `.env` changed.
3. Complete one voice turn.

**Expected Results:**

- [ ] Rose still returns text.
- [ ] The UI shows an audio-unavailable or browser-speech fallback state rather than crashing.
- [ ] No provider secret or raw provider payload is shown to the user.
- [ ] Server logs contain sanitized error details only.

Restore the valid key after the test.

---

### Test 9: Browser Console And Network Review

**Steps:**

1. Run the full checklist with the Console and Network tabs open.
2. Review failed requests and warnings.

**Expected Results:**

- [ ] No unexpected red console errors.
- [ ] No CORS errors.
- [ ] No repeated reconnect loop.
- [ ] HTTP fallback only appears when WebSocket is unavailable.
- [ ] Audio chunks are not logged to the browser console.

---

### Test 10: Latency Notes

Record observed timing after at least five successful turns:

- Browser: _____
- STT provider: _____
- P50 mic-to-first-audio: _____ ms
- P95 mic-to-first-audio: _____ ms
- P50 full turn: _____ ms
- P95 full turn: _____ ms
- Notes on audio clipping, interruption, or delayed playback:

## Test Results Summary

- [ ] Voice session starts reliably.
- [ ] WebSocket voice path works.
- [ ] HTTP voice fallback works when WebSocket is unavailable.
- [ ] Rose gives short, voice-native responses.
- [ ] Audio responses play consistently.
- [ ] Barge-in works without overlapping audio.
- [ ] Incomplete turns ask for continuation.
- [ ] Crisis safety routing is deterministic.
- [ ] Memory controls work and preserve privacy boundaries.
- [ ] Logs avoid secrets, raw audio, and raw sensitive transcripts by default.

## Post-Testing Cleanup

1. Stop the development server with Ctrl+C.
2. Restore any temporarily invalid provider keys.
3. Delete local test audio/temp files if any were manually saved outside the app.
4. Record issues with browser, provider, exact transcript, and observed timing.

## Notes

- Test in Chrome, Firefox, and Safari when possible.
- Test on at least one mobile browser before claiming mobile reliability.
- Use synthetic crisis prompts only for safety regression checks.
- Keep archived Chainlit, WhatsApp, and image-generation behavior out of this active manual guide unless those features are intentionally revived.
