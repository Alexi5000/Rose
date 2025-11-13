# 🌹 Rose Frontend

Voice-first AI grief counselor with WebGL shader background and real-time audio reactivity.

## Quick Start

```bash
# Install dependencies
npm install

# Run dev server (localhost:3000)
npm run dev

# Build for production
npm run build
```

## Architecture

### User Interaction Flow

1. **Tap anywhere on screen** → Start voice session
2. **Speak naturally** → Auto-detected via VAD
3. **Auto-records** when you speak
4. **Auto-stops** when you pause
5. **Rose responds** → Audio plays with visual feedback
6. **Tap again** → Stop session (or auto-stops after 20s inactivity)

### Tech Stack

- React 18 + TypeScript (strict mode)
- Vite 7.2 (build tool)
- Tailwind CSS 3.4
- shadcn/ui (Radix UI)
- WebGL (shader)
- Web Audio API (VAD)

## Key Features

- ✅ Full-screen voice interface (entire screen is clickable)
- ✅ Voice Activity Detection with 3-frame hysteresis
- ✅ Audio-reactive WebGL shader (pulses with voice)
- ✅ State-based color transitions (Blue → Purple → Pink)
- ✅ Automatic error handling with shadcn Alerts
- ✅ Dev settings panel (Ctrl+Shift+D)
- ✅ Desktop-first (mobile planned)

## Configuration

All VAD parameters in `src/config/voice.ts`:

```typescript
RMS_ACTIVATION_THRESHOLD = 0.02    // Speech detection
RMS_DEACTIVATION_THRESHOLD = 0.01  // Silence detection
INACTIVITY_TIMEOUT_MS = 20000      // 20s auto-stop
```

## Dev Tools

Press **Ctrl+Shift+D** to open settings panel:
- Adjust VAD thresholds
- Change timeout duration
- View real-time audio metrics

## Build Output

Builds to `../src/ai_companion/interfaces/web/static/` for backend serving.

## Browser Requirements

- Chrome/Edge 90+
- Firefox 88+
- Safari 14.1+
- Requires: WebGL, Web Audio API, MediaRecorder, getUserMedia

## Troubleshooting

**Mic permission denied?** Check browser permissions, use HTTPS

**WebGL not working?** Update graphics drivers, check browser compatibility

**Backend connection failed?** Ensure backend running on port 8000

