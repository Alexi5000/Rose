# 🌹 Rose the Healer Shaman - Claude Development Guide

> **Voice-first AI grief counselor and holistic healing companion**

## 📋 Project Overview

Rose is an immersive, empathetic AI companion designed to support users through grief and emotional healing. Built with cutting-edge voice AI, 3D visualization, and therapeutic conversation design.

### 🎯 Core Mission
Provide accessible, compassionate grief counseling through natural voice conversations in a beautifully immersive 3D environment.

### 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Three.js)              │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐     │
│  │ 3D Ice Cave │  │ Voice Button │  │ Audio Playback│     │
│  │   Scene     │  │ Push-to-Talk │  │   System      │     │
│  └─────────────┘  └──────────────┘  └───────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│              Backend API (FastAPI + LangGraph)              │
│  ┌──────────────┐  ┌────────────┐  ┌──────────────┐       │
│  │   Voice      │  │  Workflow  │  │    Memory    │       │
│  │  Processing  │  │   Graph    │  │   System     │       │
│  └──────────────┘  └────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                            ↕ API Calls
┌─────────────────────────────────────────────────────────────┐
│                    External Services                        │
│  ┌──────────┐  ┌─────────────┐  ┌─────────┐  ┌─────────┐ │
│  │   Groq   │  │ ElevenLabs  │  │ Qdrant  │  │ SQLite  │ │
│  │ LLM+STT  │  │     TTS     │  │ Vectors │  │Sessions │ │
│  └──────────┘  └─────────────┘  └─────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Node.js 20+
- Python 3.12+
- Docker & Docker Compose
- API Keys: Groq, ElevenLabs, Qdrant (optional)

### Environment Setup
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Add your API keys to .env
GROQ_API_KEY=your_groq_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
ELEVENLABS_VOICE_ID=your_voice_id_here

# 3. Start development
docker-compose up -d
```

### Access Points
- 🌐 **Frontend**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/api/v1/docs
- 🏥 **Health**: http://localhost:8000/api/v1/health
- 🗄️ **Qdrant**: http://localhost:6333

## 📁 Project Structure

```
Rose/
├── .claude/                    # Claude development tools
│   ├── commands/               # Slash commands for common tasks
│   ├── skills/                 # Reusable development skills
│   └── settings.local.json     # Claude permissions
│
├── .kiro/                      # Project specifications
│   └── specs/                  # Feature specifications
│       ├── deployment-readiness-review/
│       ├── frontend-backend-integration-fix/
│       ├── immersive-3d-frontend/
│       └── rose-transformation/
│
├── frontend/                   # React + Three.js frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   │   ├── Scene/          # 3D scene components
│   │   │   ├── UI/             # UI components (VoiceButton, etc.)
│   │   │   └── Effects/        # Visual effects
│   │   ├── hooks/              # Custom React hooks
│   │   ├── services/           # API client
│   │   ├── config/             # Configuration
│   │   └── App.tsx             # Main app component
│   ├── package.json
│   └── vite.config.ts
│
├── src/                        # Python backend
│   └── ai_companion/
│       ├── config/             # Configuration
│       │   └── server_config.py
│       ├── core/               # Core utilities
│       │   ├── logging_config.py
│       │   ├── metrics.py
│       │   └── exceptions.py
│       ├── graph/              # LangGraph workflow
│       │   ├── graph.py
│       │   └── nodes/          # Workflow nodes
│       ├── interfaces/         # API layer
│       │   └── web/
│       │       ├── app.py
│       │       └── routes/     # API endpoints
│       └── modules/            # Core modules
│           ├── memory/         # Memory system
│           ├── speech/         # STT/TTS
│           └── conversation/   # Conversation logic
│
├── docker-compose.yml          # Container orchestration
├── Dockerfile                  # Multi-stage build
├── pyproject.toml              # Python dependencies
└── README.md                   # User documentation
```

## 🎨 Development Workflows

### Voice Interaction Flow
```
User                Frontend              Backend              External APIs
  │                     │                    │                      │
  │  Press & Hold       │                    │                      │
  ├──────────────────>  │                    │                      │
  │                     │                    │                      │
  │  Speak              │  Start Recording   │                      │
  ├──────────────────>  ├─────────────────>  │                      │
  │                     │  (MediaRecorder)   │                      │
  │                     │                    │                      │
  │  Release            │  Stop & Send       │                      │
  ├──────────────────>  │  POST /voice/proc  │                      │
  │                     ├───────────────────>│                      │
  │                     │  (audio blob)      │                      │
  │                     │                    │  Transcribe (STT)    │
  │                     │                    ├─────────────────────>│
  │                     │                    │  (Groq Whisper)      │
  │                     │                    │<─────────────────────│
  │                     │                    │  "text"              │
  │                     │                    │                      │
  │                     │                    │  Process (LLM)       │
  │                     │                    ├─────────────────────>│
  │                     │                    │  (Groq Llama 3.3)    │
  │                     │                    │<─────────────────────│
  │                     │                    │  "response"          │
  │                     │                    │                      │
  │                     │                    │  Synthesize (TTS)    │
  │                     │                    ├─────────────────────>│
  │                     │                    │  (ElevenLabs)        │
  │                     │                    │<─────────────────────│
  │                     │                    │  audio bytes         │
  │                     │<───────────────────│                      │
  │                     │  {text, audio_url} │                      │
  │                     │                    │                      │
  │  Hear Response      │  Play Audio        │                      │
  │<──────────────────  │<─────────────────  │                      │
  │                     │  (Audio element)   │                      │
```

## 🧪 Testing & Verification

### Voice Button Testing
```bash
# Test the voice interaction
# 1. Open http://localhost:8000
# 2. Press and HOLD Space bar
# 3. Say: "Hello Rose, I'm feeling sad"
# 4. Release Space bar
# 5. Wait for Rose's voice response
```

### API Health Check
```bash
curl http://localhost:8000/api/v1/health
# Expected: {"status":"healthy","services":{"groq":"connected",...}}
```

### End-to-End Test
```bash
# Use Claude command
/test-voice
```

## 📚 Claude Commands Reference

### Development Commands
- `/test-voice` - Test voice interaction end-to-end
- `/check-health` - Verify all services are healthy
- `/review-logs` - Review recent application logs
- `/verify-specs` - Check alignment with .kiro specs
- `/build-prod` - Build production Docker image
- `/deploy-check` - Run deployment readiness checks

### Debugging Commands
- `/debug-voice` - Diagnose voice button issues
- `/debug-api` - Test API endpoints
- `/debug-memory` - Check memory system status
- `/check-errors` - Search for errors in logs

### Deployment Commands
- `/deploy-railway` - Deploy to Railway
- `/deploy-docker` - Build and deploy Docker containers
- `/rollback` - Rollback to previous deployment

## 🛠️ Development Standards

### Code Style
- **Python**: Black formatter, isort, pylint
- **TypeScript**: Prettier, ESLint
- **Commits**: Conventional Commits (feat:, fix:, docs:, etc.)

### Logging Standards
```python
# Use emoji logging at key points
logger.info("🎤 voice_processing_started", session_id=session_id)
logger.info("✅ workflow_execution_success", duration_ms=123.45)
logger.error("❌ speech_to_text_failed", error=str(e))
```

### Error Handling
- Custom exception hierarchy
- User-friendly error messages
- No sensitive data in errors
- Proper HTTP status codes

### Performance Targets
- Voice processing: < 10 seconds end-to-end
- Health check: < 100ms
- Frontend load: < 2 seconds
- Memory usage: < 512MB (Railway free tier)

## 🔐 Security Standards

### API Keys
- ✅ All keys in environment variables
- ✅ No keys in code or git
- ✅ Validation on startup
- ✅ Proper error messages if missing

### CORS Configuration
- Development: Localhost only
- Production: Specific domains only
- No wildcard (*) in production

### File Security
- Temporary audio files: Owner read/write only
- Automatic cleanup after 24 hours
- Size limits enforced (10MB max)

## 📊 Monitoring & Observability

### Structured Logging
All logs include:
- `session_id` - User session identifier
- `request_id` - Request trace ID
- `timestamp` - ISO 8601 format
- `event` - Descriptive event name
- `logger` - Module path

### Metrics Tracked
- `voice_request_count` - Total voice requests
- `voice_processing_duration_ms` - Processing time
- `groq_api_calls` - External API usage
- `elevenlabs_api_calls` - TTS usage
- `error_count` - Errors by type

### Health Checks
- `/api/v1/health` - Overall health
- `/api/v1/metrics` - Prometheus metrics
- Service connectivity checks (Groq, ElevenLabs, Qdrant)

## 🎯 Feature Specifications

All features are documented in `.kiro/specs/` with:
- **requirements.md** - User stories and acceptance criteria
- **design.md** - Technical design and architecture
- **tasks.md** - Implementation checklist

### Current Specs
1. **deployment-readiness-review** - Production readiness checklist
2. **frontend-backend-integration-fix** - API integration fixes
3. **immersive-3d-frontend** - 3D ice cave scene
4. **rose-transformation** - Character and therapeutic design
5. **playai-tts-migration** - TTS provider migration (planned)
6. **github-cicd-production-workflow** - CI/CD pipeline (planned)

## 🚀 Deployment

### Docker Production Build
```bash
# Build optimized image
docker-compose build rose

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f rose
```

### Railway Deployment
```bash
# Use Claude command
/deploy-railway

# Or manually:
railway up
```

### Environment Variables Required
```bash
# Core API Keys
GROQ_API_KEY=           # Groq API key for LLM and STT
ELEVENLABS_API_KEY=     # ElevenLabs API key for TTS
ELEVENLABS_VOICE_ID=    # Voice ID for Brian/Rose voice

# Optional
QDRANT_URL=             # Qdrant vector DB URL
QDRANT_API_KEY=         # Qdrant API key
PORT=8000               # Server port (default: 8000)
```

## 🐛 Troubleshooting

### Voice Button Not Working
```bash
# Run diagnostic
/debug-voice

# Common issues:
# 1. Not using "press and hold" pattern
# 2. Microphone permission denied
# 3. API keys not configured
# 4. Backend not running

# See: VOICE_TESTING_GUIDE.md
```

### Backend Not Starting
```bash
# Check logs
docker-compose logs rose

# Common issues:
# 1. Missing API keys in .env
# 2. Port 8000 already in use
# 3. Docker not running
```

### Frontend Not Loading
```bash
# Check if backend serves frontend
curl http://localhost:8000/

# Common issues:
# 1. Frontend not built (npm run build)
# 2. Static files not copied to backend
# 3. CORS issues
```

## 🎓 Learning Resources

### Key Technologies
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **FastAPI**: https://fastapi.tiangolo.com/
- **React Three Fiber**: https://docs.pmnd.rs/react-three-fiber
- **Groq**: https://console.groq.com/docs
- **ElevenLabs**: https://docs.elevenlabs.io/

### Project Documentation
- `README.md` - User-facing documentation
- `DEPLOYMENT_STATUS.md` - Current deployment status
- `DEPLOYMENT_FIXES_SUMMARY.md` - Recent fixes applied
- `VOICE_TESTING_GUIDE.md` - Voice interaction testing
- `.kiro/specs/` - Feature specifications

## 🤝 Contributing

### Before Starting
1. Read relevant `.kiro/specs/` for feature requirements
2. Check `DEPLOYMENT_STATUS.md` for current state
3. Review this CLAUDE.md for standards
4. Use `/verify-specs` to ensure alignment

### Development Process
1. Create feature branch from `main`
2. Follow code style standards
3. Add tests for new features
4. Update documentation
5. Run `/verify-specs` before committing
6. Create PR with descriptive title

### Commit Message Format
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types: feat, fix, docs, style, refactor, test, chore

## 📞 Support & Contact

### Issue Reporting
- GitHub Issues: [Create Issue](https://github.com/your-org/rose/issues)
- Include: Browser console logs, network tab screenshots
- Use diagnostic commands before reporting

### Development Help
- Use Claude commands for common tasks
- Check `.kiro/specs/` for requirements
- Review logs with `/review-logs`
- Test with `/test-voice` and `/check-health`

---

**Built with ❤️ for healing and hope**

*Last Updated: October 30, 2025*
