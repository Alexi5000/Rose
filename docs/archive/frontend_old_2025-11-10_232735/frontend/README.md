# Rose Frontend

React-based voice interface for Rose the Healer Shaman.

## Features

- Toggle-to-talk session that auto-detects speech for five minutes or until muted
- Real-time voice activity detection (RMS-based) with automatic utterance slicing
- Audio response playback with codec negotiation and autoplay recovery
- Smooth animations with Framer Motion and responsive layout
- Error handling, retry logic, and developer-friendly emoji logs

## Development

```bash
# Install dependencies
npm install

# Start development server (with API proxy)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
src/
├── components/
│   ├── UI/VoiceButton.tsx     # Toggle voice button with stateful visuals
│   ├── Scene/IceCaveScene.tsx # Primary 3D scene
│   └── ...
├── config/
│   ├── voiceTokens.ts         # Shared voice session design tokens
│   └── refinedAudio.ts        # Recording/playback constraints
├── hooks/
│   ├── useVoiceSessionController.ts  # Voice session + VAD orchestrator
│   ├── useVoicePipeline.ts           # Backend processing + playback
│   └── useAudioAnalyzer.ts           # Audio amplitude visualisation
├── services/
│   └── apiClient.ts           # Backend API client
├── utils/
│   └── audioAnalysis.ts       # RMS utilities (with Vitest coverage)
├── App.tsx                    # Main application component
└── main.tsx                   # Application entry point
```

Legacy documents and retired hooks now live under `archive/frontend-legacy/` for reference.

## Voice Session Workflow

1. Press the voice button (or hit Space/Enter) to activate Rose. The session stays hot for five minutes unless you mute manually (Escape or button).
2. Voice activity detection starts recording automatically once speech crosses the RMS threshold.
3. Each utterance is validated, queued, and sent to `POST /api/voice/process`. Responses stream back through ElevenLabs/Groq and play with autoplay-safe handling.
4. Inactivity (15 seconds of silence) or the five-minute timer mutes the session to respect the YAGNI/Uncle Bob guardrails.

## API Integration

The frontend communicates with the FastAPI backend through these endpoints:

- `POST /api/session/start` - Initialize a new session
- `POST /api/voice/process` - Process voice input and get response
- `GET /api/voice/audio/{audio_id}` - Retrieve audio response
- `GET /api/health` - Health check

## Build Configuration

The production build outputs to `../src/ai_companion/interfaces/web/static/` for serving by FastAPI.

## Testing

```bash
npm run test          # Vitest unit tests (includes audio analysis utilities)
npm run test:e2e      # Playwright smoke tests (requires dev server)
```

## Browser Support

- Chrome/Edge (recommended)
- Firefox
- Safari (iOS and macOS)

Requires browser support for:
- Web Audio API
- MediaRecorder API
- ES2020+
