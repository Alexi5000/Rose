# Rose Frontend

React-based voice interface for Rose the Healer Shaman.

## Features

- Push-to-talk voice interaction
- Real-time audio visualization
- Smooth animations with Framer Motion
- Responsive design (mobile and desktop)
- Error handling and retry logic

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
├── components/          # React components
│   ├── VoiceButton.tsx     # Main push-to-talk button
│   ├── AudioVisualizer.tsx # Audio waveform visualization
│   ├── StatusIndicator.tsx # Status messages and errors
│   └── ErrorBoundary.tsx   # Error boundary wrapper
├── hooks/              # Custom React hooks
│   ├── useVoiceRecording.ts  # Audio capture logic
│   └── useAudioPlayback.ts   # Audio playback logic
├── services/           # API and utilities
│   └── apiClient.ts          # Backend API client
├── App.tsx             # Main application component
├── App.css             # Application styles
├── main.tsx            # Application entry point
└── index.css           # Global styles
```

## API Integration

The frontend communicates with the FastAPI backend through these endpoints:

- `POST /api/session/start` - Initialize a new session
- `POST /api/voice/process` - Process voice input and get response
- `GET /api/voice/audio/{audio_id}` - Retrieve audio response
- `GET /api/health` - Health check

## Build Configuration

The production build outputs to `../src/ai_companion/interfaces/web/static/` for serving by FastAPI.

## Browser Support

- Chrome/Edge (recommended)
- Firefox
- Safari (iOS and macOS)

Requires browser support for:
- Web Audio API
- MediaRecorder API
- ES2020+
