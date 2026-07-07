# Rose Frontend

Voice-first emotional support interface with a WebGL background, browser VAD,
WebSocket audio transport, and real-time playback feedback.

Rose is not a therapist, doctor, emergency service, or clinical product. The
frontend should keep that boundary visible while making the voice experience feel
calm, responsive, and easy to leave.

## Quick Start

```bash
# Install dependencies
npm install

# Run dev server at http://localhost:3000
npm run dev

# Build for production
npm run build
```

Run the backend separately from the repository root:

```bash
uv run uvicorn ai_companion.interfaces.web.app:app --app-dir src --reload --port 8000
```

Or start frontend and backend together:

```bash
python scripts/run_dev_server.py
```

## Interaction Flow

1. Tap the interface to start a voice session.
2. Grant microphone permission.
3. Speak naturally.
4. Browser VAD records when speech is detected.
5. The client streams or uploads audio to FastAPI.
6. Rose responds with text and audio playback.
7. Tap or speak during playback to interrupt and return to listening.

## Tech Stack

- React 19 and TypeScript
- Vite 7
- Tailwind CSS 3
- shadcn/ui and Radix UI
- WebGL background rendering
- Web Audio API, MediaRecorder, and browser VAD
- WebSocket audio jitter buffer with HTTP voice fallback

## Key Features

- Full-screen voice-first interaction
- Voice activity detection with configurable hysteresis
- Audio-reactive visual state transitions
- WebSocket voice transport with HTTP fallback
- Barge-in support during Rose playback
- Session-only memory toggle
- Memory export and forget controls
- Dev settings panel with Ctrl+Shift+D

## Configuration

VAD settings live in `src/config/voice.ts`:

```typescript
RMS_ACTIVATION_THRESHOLD = 0.02;
RMS_DEACTIVATION_THRESHOLD = 0.01;
INACTIVITY_TIMEOUT_MS = 20000;
```

Backend connection helpers live in `src/lib/api.ts`. The default local API is
`http://localhost:8000`.

## Build Output

`npm run build` writes the production bundle to:

```text
../src/ai_companion/interfaces/web/static/
```

FastAPI serves that bundle in production mode when the directory exists.

## Browser Requirements

- Chrome or Edge 90+
- Firefox 88+
- Safari 14.1+
- WebGL
- Web Audio API
- MediaRecorder
- `getUserMedia`

## Troubleshooting

**Mic permission denied:** check browser permissions. Some browsers require
HTTPS outside localhost.

**WebGL unavailable:** update graphics drivers or try another supported browser.

**Backend connection failed:** confirm the FastAPI backend is running on port
8000 and that `/api/v1/health` responds.

**No voice playback:** check the TTS provider key, browser autoplay policy, and
the Network tab for `audio_unavailable` or failed audio responses.
