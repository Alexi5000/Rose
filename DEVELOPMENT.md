# 🚀 Rose Development Guide

This guide provides detailed instructions for developing Rose the Healer Shaman locally. For general project information, see [README.md](README.md).

## Quick Start

### Prerequisites

- Python 3.12 or higher
- Node.js 18+ and npm
- `uv` package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- API keys for Groq, ElevenLabs, and Qdrant

### Initial Setup

```bash
# 1️⃣ Clone and navigate to project
git clone <repository-url>
cd ai-companion

# 2️⃣ Install Python dependencies
uv sync

# 3️⃣ Install frontend dependencies
cd frontend
npm install
cd ..

# 4️⃣ Configure environment variables
cp .env.example .env
# Edit .env and add your API keys:
# - GROQ_API_KEY
# - ELEVENLABS_API_KEY
# - ELEVENLABS_VOICE_ID
# - QDRANT_URL
# - QDRANT_API_KEY

# 5️⃣ Configure frontend environment
cp frontend/.env.example frontend/.env
# Default values should work for local development
```

## Development Mode (Hot Reload)

Development mode runs both the frontend and backend with hot reload enabled, allowing you to see changes immediately without rebuilding.

### Option 1: Unified Development Server (Recommended)

Start both frontend and backend with a single command:

```bash
python scripts/run_dev_server.py
```

This starts:
- 🎨 **Frontend**: http://localhost:3000 (Vite dev server with hot reload)
- 🔌 **Backend**: http://localhost:8000 (FastAPI with auto-reload)
- 📚 **API Docs**: http://localhost:8000/api/v1/docs (Swagger UI)

The frontend automatically proxies API requests to the backend, so you can develop both simultaneously.

**To stop**: Press `Ctrl+C` in the terminal

### Option 2: Manual Server Management

If you prefer to run servers separately (useful for debugging):

**Terminal 1 - Backend:**
```bash
uv run uvicorn ai_companion.interfaces.web.app:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Development Workflow

1. **Make changes** to Python or TypeScript files
2. **Save the file** - changes are automatically detected
3. **Refresh browser** (frontend hot-reloads automatically)
4. **Check logs** in the terminal for any errors

### Development Features

- ✅ Hot reload for both frontend and backend
- ✅ Source maps for debugging
- ✅ Detailed error messages
- ✅ API request logging with emoji indicators
- ✅ CORS enabled for cross-origin requests

## Production Mode

Production mode builds an optimized frontend bundle and serves it through the FastAPI backend.

### Build and Serve

```bash
python scripts/build_and_serve.py
```

This will:
1. 🎨 Build the frontend with optimizations (minification, tree-shaking)
2. 📦 Output to `src/ai_companion/interfaces/web/static/`
3. 🚀 Start the FastAPI server on http://localhost:8000

The server serves both the static frontend files and the API endpoints.

### Manual Production Build

If you need to build without starting the server:

```bash
# Build frontend only
cd frontend
npm run build
cd ..

# Start production server
uv run uvicorn ai_companion.interfaces.web.app:app --host 0.0.0.0 --port 8000
```

### Production Features

- ✅ Minified and optimized assets
- ✅ Long-term caching for static assets (1 year)
- ✅ Gzip compression
- ✅ Single-page application routing
- ✅ Production error handling

## Project Structure

```
ai-companion/
├── src/ai_companion/           # Python backend
│   ├── config/                 # Configuration constants
│   │   └── server_config.py    # Server configuration (ports, paths, timeouts)
│   ├── core/                   # Core utilities
│   │   ├── prompts.py          # Rose's personality and system prompts
│   │   ├── schedules.py        # Activity scheduling
│   │   └── exceptions.py       # Custom exceptions
│   ├── graph/                  # LangGraph workflow
│   │   ├── graph.py            # Workflow orchestration
│   │   ├── state.py            # State management
│   │   ├── nodes.py            # Processing nodes
│   │   └── edges.py            # Conditional routing
│   ├── interfaces/             # User interfaces
│   │   └── web/                # FastAPI web interface
│   │       ├── app.py          # Main FastAPI application
│   │       ├── routes/         # API route handlers
│   │       └── static/         # Frontend build output (generated)
│   ├── modules/                # Feature modules
│   │   ├── memory/             # Long-term and short-term memory
│   │   └── speech/             # Speech-to-text and text-to-speech
│   └── settings.py             # Application settings
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   │   ├── Scene/          # 3D scene components
│   │   │   └── UI/             # UI components (buttons, loading)
│   │   ├── hooks/              # Custom React hooks
│   │   │   ├── useVoiceInteraction.ts  # Voice recording/playback
│   │   │   ├── useHealthCheck.ts       # Backend health check
│   │   │   └── useAssetLoader.ts       # Asset loading
│   │   ├── services/           # API clients
│   │   │   └── apiClient.ts    # Axios-based API client
│   │   ├── config/             # Frontend configuration
│   │   │   └── errorMessages.ts # User-facing error messages
│   │   └── App.tsx             # Main application component
│   ├── vite.config.ts          # Vite build configuration
│   └── package.json            # Frontend dependencies
│
├── scripts/                    # Development scripts
│   ├── run_dev_server.py       # Start dev servers
│   └── build_and_serve.py      # Build and serve production
│
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── conftest.py             # Test configuration
│
└── docs/                       # Documentation
```

## Configuration

### Backend Configuration

All backend configuration constants are centralized in `src/ai_companion/config/server_config.py`:

```python
# 🌐 Network Configuration
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = 8000
DEV_FRONTEND_PORT = 3000

# 📁 Path Configuration
FRONTEND_BUILD_DIR = PROJECT_ROOT / "src" / "ai_companion" / "interfaces" / "web" / "static"

# ⏱️ Timeout Configuration
API_REQUEST_TIMEOUT_SECONDS = 60
WORKFLOW_TIMEOUT_SECONDS = 55

# 📦 File Size Limits
MAX_AUDIO_FILE_SIZE_MB = 10
```

### Frontend Configuration

Frontend configuration is in `frontend/.env`:

```bash
# API endpoint (automatically set for development)
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### Environment Variables Reference

This section provides a comprehensive reference for all environment variables used by Rose the Healer Shaman.

#### 🔑 Required API Keys

These API keys are **required** for the application to function:

**`GROQ_API_KEY`**
- **Purpose**: API key for Groq services (LLM inference and speech-to-text)
- **Example**: `gsk_YOUR_API_KEY_HERE`
- **Get it from**: https://console.groq.com/keys
- **Used for**: Text generation, conversation processing, voice transcription

**`ELEVENLABS_API_KEY`**
- **Purpose**: API key for ElevenLabs text-to-speech service (Rose's voice)
- **Example**: `your_elevenlabs_api_key`
- **Get it from**: https://elevenlabs.io/app/settings/api-keys
- **Used for**: Converting Rose's text responses to natural-sounding speech

**`ELEVENLABS_VOICE_ID`**
- **Purpose**: Voice ID for ElevenLabs TTS (determines Rose's voice characteristics)
- **Example**: `21m00Tcm4TlvDq8ikWAM` (Rachel voice)
- **Get it from**: https://elevenlabs.io/app/voice-library
- **Recommendation**: Choose a warm, calming female voice for therapeutic interactions

**`QDRANT_URL`**
- **Purpose**: URL for Qdrant vector database (long-term memory storage)
- **Example (Cloud)**: `https://your-cluster.qdrant.io`
- **Example (Local)**: `http://localhost:6333`
- **Example (Docker)**: `http://qdrant:6333`
- **Get it from**: https://cloud.qdrant.io (for cloud) or run locally with Docker
- **Used for**: Storing and retrieving conversation memories

**`QDRANT_API_KEY`**
- **Purpose**: API key for Qdrant cloud (leave empty for local Qdrant)
- **Example**: `your_qdrant_api_key`
- **Required**: Only for Qdrant Cloud, not needed for local Docker deployment
- **Get it from**: https://cloud.qdrant.io

**`TOGETHER_API_KEY`**
- **Purpose**: API key for Together AI image generation (frozen feature)
- **Example**: `your_together_api_key`
- **Get it from**: https://api.together.xyz/settings/api-keys
- **Note**: Image generation is currently disabled in Rose's voice-first release

---

#### 🎭 Rose-Specific Configuration

**`ROSE_VOICE_ID`** (Optional)
- **Purpose**: Override `ELEVENLABS_VOICE_ID` specifically for Rose's healing voice
- **Example**: `21m00Tcm4TlvDq8ikWAM`
- **Default**: Uses `ELEVENLABS_VOICE_ID` if not set
- **Recommendation**: Use a warm, empathetic voice optimized for therapeutic conversations

---

#### 🌐 Server Configuration

**`PORT`**
- **Purpose**: HTTP server port number
- **Example**: `8080`
- **Default**: `8000`
- **Note**: Automatically set by Railway in production deployments

**`HOST`**
- **Purpose**: Server host address to bind to
- **Example**: `0.0.0.0` (all interfaces) or `127.0.0.1` (localhost only)
- **Default**: `0.0.0.0`
- **Production**: Use `0.0.0.0` to accept external connections
- **Development**: Use `127.0.0.1` for local-only access

---

#### 🔒 Security Configuration

**`ALLOWED_ORIGINS`**
- **Purpose**: CORS allowed origins (comma-separated list)
- **Example (Development)**: `*` or `http://localhost:3000,http://localhost:5173`
- **Example (Production)**: `https://yourdomain.com,https://www.yourdomain.com`
- **Default**: `*` (allow all origins)
- **Security**: Set to specific domains in production to prevent unauthorized access

**`RATE_LIMIT_ENABLED`**
- **Purpose**: Enable/disable rate limiting globally
- **Example**: `true` or `false`
- **Default**: `true`
- **Recommendation**: Keep enabled in production to prevent abuse

**`RATE_LIMIT_PER_MINUTE`**
- **Purpose**: Maximum requests per minute per IP address
- **Example**: `10`
- **Default**: `10`
- **Adjust**: Increase for high-traffic applications, decrease for stricter limits

**`ENABLE_SECURITY_HEADERS`**
- **Purpose**: Enable security headers (CSP, HSTS, X-Frame-Options, etc.)
- **Example**: `true` or `false`
- **Default**: `true`
- **Recommendation**: Keep enabled in production for security best practices

---

#### ⏱️ Workflow Configuration

**`WORKFLOW_TIMEOUT_SECONDS`**
- **Purpose**: Global timeout for LangGraph workflow execution
- **Example**: `60`
- **Default**: `55`
- **Range**: 30-120 seconds recommended
- **Purpose**: Prevents hanging requests and resource exhaustion

---

#### 🤖 Model Configuration

**`TEXT_MODEL_NAME`**
- **Purpose**: Primary LLM model for conversation and response generation
- **Example**: `llama-3.3-70b-versatile`
- **Default**: `llama-3.3-70b-versatile`
- **Options**: Any Groq-supported model (see https://console.groq.com/docs/models)

**`SMALL_TEXT_MODEL_NAME`**
- **Purpose**: Smaller/faster LLM for routing and simple tasks
- **Example**: `llama-3.1-8b-instant`
- **Default**: `llama-3.1-8b-instant`
- **Purpose**: Reduces latency and cost for non-critical operations

**`STT_MODEL_NAME`**
- **Purpose**: Speech-to-text model for voice transcription
- **Example**: `whisper-large-v3`
- **Default**: `whisper-large-v3`
- **Options**: `whisper-large-v3`, `whisper-large-v3-turbo`

**`TTS_MODEL_NAME`**
- **Purpose**: Text-to-speech model for audio generation
- **Example**: `eleven_flash_v2_5`
- **Default**: `eleven_flash_v2_5`
- **Options**: ElevenLabs model names (see https://elevenlabs.io/docs/api-reference/models)

**`TTI_MODEL_NAME`**
- **Purpose**: Text-to-image model for image generation (frozen feature)
- **Example**: `black-forest-labs/FLUX.1-schnell-Free`
- **Default**: `black-forest-labs/FLUX.1-schnell-Free`
- **Note**: Image generation is currently disabled

**`ITT_MODEL_NAME`**
- **Purpose**: Image-to-text model for vision tasks (frozen feature)
- **Example**: `llama-3.2-90b-vision-preview`
- **Default**: `llama-3.2-90b-vision-preview`
- **Note**: Vision features are currently disabled

---

#### 🧠 Memory Configuration

**`MEMORY_TOP_K`**
- **Purpose**: Number of relevant memories to retrieve for context
- **Example**: `3`
- **Default**: `3`
- **Range**: 1-20 (higher values provide more context but increase latency)

**`ROUTER_MESSAGES_TO_ANALYZE`**
- **Purpose**: Number of recent messages to analyze for routing decisions
- **Example**: `3`
- **Default**: `3`

**`TOTAL_MESSAGES_SUMMARY_TRIGGER`**
- **Purpose**: Trigger conversation summarization after this many messages
- **Example**: `20`
- **Default**: `20`
- **Purpose**: Prevents conversation history from growing too large

**`TOTAL_MESSAGES_AFTER_SUMMARY`**
- **Purpose**: Number of messages to keep after summarization
- **Example**: `5`
- **Default**: `5`

**`SHORT_TERM_MEMORY_DB_PATH`**
- **Purpose**: Filesystem path for SQLite short-term memory database
- **Example**: `/app/data/memory.db`
- **Default**: `/app/data/memory.db`
- **Note**: Automatically created if it doesn't exist

---

#### 📊 Logging Configuration

**`LOG_LEVEL`**
- **Purpose**: Logging verbosity level
- **Example**: `INFO`
- **Default**: `INFO`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Development**: Use `DEBUG` for detailed logs
- **Production**: Use `INFO` or `WARNING` to reduce noise

**`LOG_FORMAT`**
- **Purpose**: Log output format
- **Example**: `json`
- **Default**: `json`
- **Options**: `json` (structured logging) or `console` (human-readable)
- **Production**: Use `json` for log aggregation and parsing
- **Development**: Use `console` for easier reading

---

#### 📚 API Documentation

**`ENABLE_API_DOCS`**
- **Purpose**: Enable/disable OpenAPI/Swagger documentation
- **Example**: `true` or `false`
- **Default**: `true`
- **Access**: http://localhost:8000/api/v1/docs (Swagger UI)
- **Security**: Set to `false` in production if you want to hide API docs

---

#### 📦 Resource Management

**`MAX_REQUEST_SIZE`**
- **Purpose**: Maximum HTTP request body size in bytes
- **Example**: `10485760` (10MB)
- **Default**: `10485760` (10MB)
- **Purpose**: Prevents memory exhaustion from large payloads

**`SESSION_RETENTION_DAYS`**
- **Purpose**: Delete sessions older than this many days
- **Example**: `7`
- **Default**: `7`
- **Purpose**: Automatic cleanup runs daily at 3 AM

---

#### 🚩 Feature Flags

Feature flags allow you to enable/disable features without code changes.

**`FEATURE_WHATSAPP_ENABLED`**
- **Purpose**: Enable WhatsApp integration (frozen for future release)
- **Example**: `false`
- **Default**: `false`
- **Note**: Requires WhatsApp credentials (see below)

**`FEATURE_IMAGE_GENERATION_ENABLED`**
- **Purpose**: Enable image generation (frozen for future release)
- **Example**: `false`
- **Default**: `false`
- **Note**: Currently disabled in voice-first release

**`FEATURE_TTS_CACHE_ENABLED`**
- **Purpose**: Enable caching of TTS responses
- **Example**: `true`
- **Default**: `true`
- **Recommendation**: Keep enabled to reduce API costs and latency

**`FEATURE_DATABASE_TYPE`**
- **Purpose**: Database backend selection
- **Example**: `sqlite` or `postgresql`
- **Default**: `sqlite`
- **Options**: `sqlite` (single instance) or `postgresql` (horizontal scaling)

**`FEATURE_SESSION_AFFINITY_ENABLED`**
- **Purpose**: Enable sticky sessions for load balancing
- **Example**: `false`
- **Default**: `false`
- **Use case**: Multi-instance deployments with session state

**`FEATURE_READ_REPLICA_ENABLED`**
- **Purpose**: Use read replicas for database queries
- **Example**: `false`
- **Default**: `false`
- **Requires**: PostgreSQL and `DATABASE_READ_REPLICA_URL`

**`FEATURE_MULTI_REGION_ENABLED`**
- **Purpose**: Enable multi-region routing
- **Example**: `false`
- **Default**: `false`
- **Requires**: Regional database URLs

---

#### 🗄️ Database Configuration (PostgreSQL)

These settings are only required when `FEATURE_DATABASE_TYPE=postgresql`.

**`DATABASE_URL`**
- **Purpose**: PostgreSQL connection string
- **Example**: `postgresql://user:password@host:port/database`
- **Format**: `postgresql://[user]:[password]@[host]:[port]/[database]`
- **Required**: Only when using PostgreSQL

**`DATABASE_READ_REPLICA_URL`**
- **Purpose**: Read replica connection string for query optimization
- **Example**: `postgresql://user:password@replica-host:port/database`
- **Required**: Only when `FEATURE_READ_REPLICA_ENABLED=true`

**`DATABASE_POOL_SIZE`**
- **Purpose**: Connection pool size
- **Example**: `10`
- **Default**: `10`
- **Adjust**: Increase for high-traffic applications

**`DATABASE_MAX_OVERFLOW`**
- **Purpose**: Maximum overflow connections beyond pool size
- **Example**: `20`
- **Default**: `20`

**`DATABASE_URL_US`**, **`DATABASE_URL_EU`**, **`DATABASE_URL_ASIA`**
- **Purpose**: Regional database URLs for multi-region deployments
- **Example**: `postgresql://user:password@us-host:port/database`
- **Required**: Only when `FEATURE_MULTI_REGION_ENABLED=true`

---

#### 📡 Monitoring and Alerting

**`SENTRY_DSN`**
- **Purpose**: Sentry DSN for error tracking and monitoring
- **Example**: `https://[key]@[org].ingest.sentry.io/[project]`
- **Get it from**: https://sentry.io
- **Recommendation**: Enable in staging and production for observability

**`SENTRY_TRACES_SAMPLE_RATE`**
- **Purpose**: Percentage of transactions to trace (0.0-1.0)
- **Example**: `0.1` (10%)
- **Default**: `0.1`
- **Adjust**: Lower values reduce overhead but may miss issues

**`SENTRY_PROFILES_SAMPLE_RATE`**
- **Purpose**: Percentage of transactions to profile (0.0-1.0)
- **Example**: `0.1` (10%)
- **Default**: `0.1`

**`ENVIRONMENT`**
- **Purpose**: Environment name for tracking
- **Example**: `production`, `staging`, `development`
- **Default**: `production`
- **Purpose**: Helps filter errors and metrics by environment

**`APP_VERSION`**
- **Purpose**: Application version for release tracking
- **Example**: `1.0.0`
- **Default**: `1.0.0`
- **Purpose**: Track which version caused errors

**Alert Configuration:**

- **`ALERT_ERROR_RATE_ENABLED`**: Enable error rate alerts (default: `true`)
- **`ALERT_ERROR_RATE_THRESHOLD`**: Error rate threshold percentage (default: `5.0`)
- **`ALERT_RESPONSE_TIME_ENABLED`**: Enable response time alerts (default: `true`)
- **`ALERT_RESPONSE_TIME_THRESHOLD`**: Response time threshold in ms (default: `2000.0`)
- **`ALERT_MEMORY_ENABLED`**: Enable memory usage alerts (default: `true`)
- **`ALERT_MEMORY_THRESHOLD`**: Memory usage threshold percentage (default: `80.0`)
- **`ALERT_CIRCUIT_BREAKER_ENABLED`**: Enable circuit breaker alerts (default: `true`)

**`MONITORING_EVALUATION_INTERVAL`**
- **Purpose**: Seconds between alert evaluations
- **Example**: `60`
- **Default**: `60`

---

#### 🎤 Speech-to-Text Configuration

**`STT_MAX_RETRIES`**
- **Purpose**: Maximum retry attempts for STT API calls
- **Example**: `3`
- **Default**: `3`

**`STT_INITIAL_BACKOFF`**
- **Purpose**: Initial backoff delay in seconds for retries
- **Example**: `1.0`
- **Default**: `1.0`

**`STT_MAX_BACKOFF`**
- **Purpose**: Maximum backoff delay in seconds
- **Example**: `10.0`
- **Default**: `10.0`

**`STT_TIMEOUT`**
- **Purpose**: API timeout for STT requests in seconds
- **Example**: `60`
- **Default**: `60`

**`STT_MAX_AUDIO_SIZE_MB`**
- **Purpose**: Maximum audio file size for STT in megabytes
- **Example**: `25`
- **Default**: `25`

---

#### 🔊 Text-to-Speech Configuration

**`TTS_CACHE_ENABLED`**
- **Purpose**: Enable caching of TTS responses
- **Example**: `true`
- **Default**: `true`

**`TTS_CACHE_TTL_HOURS`**
- **Purpose**: Cache time-to-live in hours
- **Example**: `24`
- **Default**: `24`

**`TTS_VOICE_STABILITY`**
- **Purpose**: Voice stability parameter (0.0-1.0)
- **Example**: `0.75`
- **Default**: `0.75`
- **Higher values**: More consistent voice
- **Lower values**: More expressive voice

**`TTS_VOICE_SIMILARITY`**
- **Purpose**: Voice similarity boost (0.0-1.0)
- **Example**: `0.5`
- **Default**: `0.5`

**`TTS_MAX_TEXT_LENGTH`**
- **Purpose**: Maximum text length for TTS in characters
- **Example**: `5000`
- **Default**: `5000`

---

#### 🧹 Cleanup Configuration

**`AUDIO_CLEANUP_MAX_AGE_HOURS`**
- **Purpose**: Delete audio files older than this many hours
- **Example**: `24`
- **Default**: `24`
- **Purpose**: Prevents disk space exhaustion from temporary audio files

---

#### 🛡️ Circuit Breaker Configuration

**`CIRCUIT_BREAKER_FAILURE_THRESHOLD`**
- **Purpose**: Number of failures before opening circuit
- **Example**: `5`
- **Default**: `5`
- **Range**: 1-10 (lower values make circuit breaker more sensitive)

**`CIRCUIT_BREAKER_RECOVERY_TIMEOUT`**
- **Purpose**: Seconds before attempting recovery
- **Example**: `60`
- **Default**: `60`

---

#### 🤖 LLM Configuration

**`LLM_TIMEOUT_SECONDS`**
- **Purpose**: Timeout for LLM API calls in seconds
- **Example**: `30.0`
- **Default**: `30.0`

**`LLM_MAX_RETRIES`**
- **Purpose**: Maximum retry attempts for LLM calls
- **Example**: `3`
- **Default**: `3`

**Temperature Settings** (0.0-1.0, higher = more creative):

- **`LLM_TEMPERATURE_DEFAULT`**: Default temperature (default: `0.7`)
- **`LLM_TEMPERATURE_ROUTER`**: Routing decisions (default: `0.3`)
- **`LLM_TEMPERATURE_MEMORY`**: Memory extraction (default: `0.1`)
- **`LLM_TEMPERATURE_IMAGE_SCENARIO`**: Image scenarios (default: `0.4`)
- **`LLM_TEMPERATURE_IMAGE_PROMPT`**: Image prompts (default: `0.25`)

---

#### 📱 WhatsApp Configuration (Optional - Frozen Feature)

These are only required when `FEATURE_WHATSAPP_ENABLED=true`.

**`WHATSAPP_PHONE_NUMBER_ID`**
- **Purpose**: WhatsApp Business phone number ID
- **Example**: `your_phone_number_id`
- **Get it from**: Meta Business Manager

**`WHATSAPP_TOKEN`**
- **Purpose**: WhatsApp API access token
- **Example**: `your_whatsapp_token`
- **Get it from**: Meta Business Manager

**`WHATSAPP_VERIFY_TOKEN`**
- **Purpose**: Webhook verification token
- **Example**: `your_verify_token`
- **Purpose**: Secures webhook endpoint

---

#### 🎨 Frontend Configuration

Frontend environment variables are defined in `frontend/.env`:

**`VITE_API_BASE_URL`**
- **Purpose**: Base URL for API requests
- **Example (Development)**: `http://localhost:8000/api/v1`
- **Example (Production)**: `https://api.yourdomain.com/api/v1`
- **Default**: `http://localhost:8000/api/v1`

**`VITE_ASSET_CDN_URL`** (Optional)
- **Purpose**: CDN URL for serving static assets
- **Example**: `https://cdn.example.com`
- **Default**: Empty (serve from same origin)
- **Use case**: Production deployments with CDN

**`VITE_ENABLE_ANALYTICS`**
- **Purpose**: Enable analytics tracking
- **Example**: `false` (development), `true` (production)
- **Default**: `false`

**`VITE_ENABLE_DEBUG`**
- **Purpose**: Enable debug logging in browser console
- **Example**: `true` (development), `false` (production)
- **Default**: `true`

**`VITE_TARGET_FPS`**
- **Purpose**: Target frames per second for desktop devices
- **Example**: `60`
- **Default**: `60`

**`VITE_MOBILE_TARGET_FPS`**
- **Purpose**: Target frames per second for mobile devices
- **Example**: `30`
- **Default**: `30`
- **Purpose**: Better battery life on mobile

---

### Configuration Examples

#### Minimal Development Setup

```bash
# .env (backend)
GROQ_API_KEY=gsk_your_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
TOGETHER_API_KEY=your_together_key
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
LOG_LEVEL=DEBUG
LOG_FORMAT=console
```

```bash
# frontend/.env (frontend)
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_ENABLE_DEBUG=true
```

#### Production Setup

```bash
# .env (backend)
GROQ_API_KEY=gsk_your_production_key
ELEVENLABS_API_KEY=your_production_key
ELEVENLABS_VOICE_ID=your_production_voice
TOGETHER_API_KEY=your_production_key
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_key

# Server
PORT=8080
HOST=0.0.0.0
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Security
RATE_LIMIT_ENABLED=true
ENABLE_SECURITY_HEADERS=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
ENVIRONMENT=production
APP_VERSION=1.0.0

# Features
FEATURE_TTS_CACHE_ENABLED=true
```

```bash
# frontend/.env (frontend)
VITE_API_BASE_URL=https://api.yourdomain.com/api/v1
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_DEBUG=false
```

---

### Configuration Validation

The application validates all configuration on startup and provides clear error messages if required settings are missing or invalid. Check the logs for:

- ✅ Configuration loaded successfully
- ❌ Missing required environment variables
- ⚠️ Optional services unavailable (warnings only)

To test your configuration:

```bash
# Backend validation
uv run python -c "from ai_companion.settings import settings; print('✅ Configuration valid')"

# Frontend validation (build test)
cd frontend && npm run build
```

## Code Quality

### Formatting and Linting

```bash
# Format code with ruff
make format-fix

# Fix linting issues
make lint-fix

# Check formatting (CI)
make format-check

# Check linting (CI)
make lint-check
```

### Pre-commit Hooks

Install pre-commit hooks to automatically format and lint on commit:

```bash
uv run pre-commit install
```

### Code Style

- **Line length**: 120 characters
- **Import sorting**: Enabled via ruff
- **Type hints**: Required for all functions
- **Docstrings**: Required for public APIs

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test categories
uv run pytest tests/unit/                    # Unit tests
uv run pytest tests/integration/             # Integration tests
uv run pytest tests/test_performance_benchmarks.py  # Performance

# Run type checking
uv run mypy src/
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

### Test Organization

- `tests/unit/` - Unit tests for individual modules
- `tests/integration/` - End-to-end workflow tests
- `tests/fixtures/` - Shared test fixtures
- `frontend/src/**/*.test.ts` - Frontend component tests

## Debugging

### Backend Debugging

**Enable debug logging:**
```bash
# In .env
LOG_LEVEL=DEBUG
```

**Use Python debugger:**
```python
import pdb; pdb.set_trace()
```

**Check logs:**
- All logs include emoji indicators for easy scanning
- 🚀 = Startup
- ✅ = Success
- ❌ = Error
- 🔌 = Connection
- 🎨 = Frontend
- 🎤 = Voice processing

### Frontend Debugging

**Browser DevTools:**
- Open DevTools (F12)
- Check Console for logs
- Check Network tab for API requests
- Check Application tab for storage

**React DevTools:**
- Install React DevTools browser extension
- Inspect component state and props

### Common Issues

See [Troubleshooting](#troubleshooting) section below.

## API Documentation

### Interactive API Docs

When the backend is running, access interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

### Key Endpoints

```
GET  /api/v1/health              # Health check
POST /api/v1/session/start       # Start new session
POST /api/v1/voice/process       # Process voice input
```

## Troubleshooting

This section covers common issues you might encounter during development and their solutions.

### 🔌 Connection Issues

#### ❌ "Cannot connect to Rose" / Backend Unreachable

**Symptoms**:
- Frontend displays "Cannot connect to Rose. Please ensure the server is running."
- Health check fails on app startup
- API requests timeout or return network errors
- Browser console shows `ERR_CONNECTION_REFUSED` or `Failed to fetch`

**Root Causes**:
- Backend server is not running
- Backend is running on wrong port
- CORS configuration blocking requests
- Firewall or network issues

**Solutions**:

1. ✅ **Verify backend is running**
   ```bash
   # Check if process is listening on port 8000
   # Windows:
   netstat -ano | findstr :8000
   
   # Linux/Mac:
   lsof -i :8000
   ```

2. ✅ **Start the backend server**
   ```bash
   # Option 1: Use unified dev server
   python scripts/run_dev_server.py
   
   # Option 2: Start backend only
   uv run uvicorn ai_companion.interfaces.web.app:app --reload --port 8000
   ```

3. ✅ **Check API base URL configuration**
   ```bash
   # Verify frontend/.env contains:
   VITE_API_BASE_URL=http://localhost:8000/api/v1
   ```

4. ✅ **Verify CORS settings**
   - Check `src/ai_companion/config/server_config.py` includes:
     ```python
     DEV_ALLOWED_ORIGINS = [
         "http://localhost:3000",
         "http://127.0.0.1:3000",
     ]
     ```
   - Restart backend after changing CORS settings

5. ✅ **Test backend directly**
   ```bash
   # Test health endpoint
   curl http://localhost:8000/api/v1/health
   
   # Should return: {"status": "healthy", "version": "1.0.0"}
   ```

6. ✅ **Check browser console**
   - Open DevTools (F12) → Console tab
   - Look for specific error messages
   - Check Network tab for failed requests

7. ✅ **Disable browser extensions**
   - Ad blockers or privacy extensions may block requests
   - Try in incognito/private mode

**Prevention**:
- Always use `python scripts/run_dev_server.py` to ensure both servers start
- Check terminal logs for 🔌 and ✅ emoji indicators showing successful startup

---

### 🎨 Asset Loading Issues

#### ❌ "Styles not loading" / Missing CSS

**Symptoms**:
- Page loads but has no styling (plain HTML)
- Text is unstyled, buttons look wrong
- Background is white instead of themed
- Browser console shows 404 errors for CSS files

**Root Causes**:
- Frontend not built or built to wrong directory
- Static file serving path misconfigured
- Build output directory doesn't exist
- Cache serving stale files

**Solutions**:

1. ✅ **Rebuild the frontend**
   ```bash
   cd frontend
   npm run build
   cd ..
   ```
   - Look for 🎨 emoji in build logs
   - Verify "✅ Build complete!" message

2. ✅ **Verify build output location**
   ```bash
   # Check that these files exist:
   ls src/ai_companion/interfaces/web/static/index.html
   ls src/ai_companion/interfaces/web/static/assets/
   ```

3. ✅ **Check Vite configuration**
   - Open `frontend/vite.config.ts`
   - Verify `outDir` points to: `../src/ai_companion/interfaces/web/static`
   - Verify `emptyOutDir: true` is set

4. ✅ **Clear browser cache**
   ```bash
   # Hard refresh (clears cache)
   # Windows/Linux: Ctrl + Shift + R
   # Mac: Cmd + Shift + R
   ```

5. ✅ **Check backend static file serving**
   - Open `src/ai_companion/interfaces/web/app.py`
   - Look for log message: "✅ Frontend build found"
   - If you see "❌ Frontend build not found", rebuild frontend

6. ✅ **Verify file permissions**
   ```bash
   # Ensure static files are readable
   # Linux/Mac:
   chmod -R 755 src/ai_companion/interfaces/web/static/
   ```

7. ✅ **Check browser DevTools**
   - Open DevTools (F12) → Network tab
   - Reload page and look for 404 errors
   - Check which files are failing to load

**Prevention**:
- Run `python scripts/build_and_serve.py` for production mode (builds automatically)
- Use `python scripts/run_dev_server.py` for development (no build needed)

#### ❌ 3D Scene Not Rendering / Black Screen

**Symptoms**:
- Page loads but 3D scene is black or missing
- Loading screen shows but never completes
- Browser console shows WebGL errors
- Assets fail to load (models, textures)

**Root Causes**:
- 3D model files not loaded
- WebGL not supported or disabled
- Asset paths incorrect
- GPU/graphics driver issues

**Solutions**:

1. ✅ **Check asset loading logs**
   - Open browser console (F12)
   - Look for 🎭 emoji (3D models) and 🎨 emoji (textures)
   - Check for "Asset loaded successfully" messages

2. ✅ **Verify WebGL support**
   ```bash
   # Test WebGL at: https://get.webgl.org/
   # Should show spinning cube
   ```

3. ✅ **Enable WebGL in browser**
   - Chrome: `chrome://flags/#ignore-gpu-blocklist` → Enable
   - Firefox: `about:config` → `webgl.disabled` → false

4. ✅ **Check GPU acceleration**
   - Chrome: `chrome://gpu/` → Check for errors
   - Update graphics drivers if needed

5. ✅ **Verify asset files exist**
   ```bash
   # Check that 3D models are in build output
   ls src/ai_companion/interfaces/web/static/assets/*.glb
   ls src/ai_companion/interfaces/web/static/assets/*.gltf
   ```

6. ✅ **Check loading screen component**
   - Open `frontend/src/components/UI/LoadingScreen.tsx`
   - Verify progress updates are working
   - Check for error states

7. ✅ **Try different browser**
   - Test in Chrome, Firefox, or Edge
   - Some browsers have better WebGL support

**Prevention**:
- Always rebuild frontend after modifying 3D assets
- Test in multiple browsers during development

---

### 🎤 Voice Processing Issues

#### ❌ "Voice processing error" / Microphone Issues

**Symptoms**:
- Voice button doesn't respond
- "Microphone access denied" error
- Recording starts but nothing happens
- Audio doesn't play back
- Backend returns 400/500 errors

**Root Causes**:
- Microphone permission denied
- No microphone connected
- Groq API key missing or invalid
- Audio file too large
- Backend processing timeout

**Solutions**:

1. ✅ **Grant microphone permission**
   - Click voice button
   - Browser will prompt for permission
   - Click "Allow" or "Grant"
   - **Chrome**: Settings → Privacy → Site Settings → Microphone
   - **Firefox**: Preferences → Privacy & Security → Permissions → Microphone

2. ✅ **Test microphone hardware**
   ```bash
   # Test at: https://www.onlinemictest.com/
   # Should see audio levels moving
   ```

3. ✅ **Check microphone is connected**
   - Windows: Settings → System → Sound → Input
   - Mac: System Preferences → Sound → Input
   - Linux: `arecord -l` to list devices

4. ✅ **Verify Groq API key**
   ```bash
   # Check .env file contains:
   GROQ_API_KEY=gsk_...
   
   # Test API key:
   curl https://api.groq.com/openai/v1/models \
     -H "Authorization: Bearer $GROQ_API_KEY"
   ```

5. ✅ **Check backend logs**
   - Look for 🎤 emoji (voice processing start)
   - Look for ❌ emoji (errors)
   - Check for specific error messages

6. ✅ **Verify audio file size**
   - Max size: 10MB (configurable in `server_config.py`)
   - Keep recordings under 1 minute
   - Check `MAX_AUDIO_FILE_SIZE_MB` constant

7. ✅ **Test with shorter recording**
   - Try 5-10 second recording first
   - Longer recordings may timeout

8. ✅ **Check API timeout settings**
   - Open `src/ai_companion/config/server_config.py`
   - Verify `API_REQUEST_TIMEOUT_SECONDS = 60`
   - Increase if needed for longer processing

9. ✅ **Verify ElevenLabs configuration** (for audio playback)
   ```bash
   # Check .env file contains:
   ELEVENLABS_API_KEY=...
   ELEVENLABS_VOICE_ID=...
   ```

10. ✅ **Check browser audio permissions**
    - Ensure site can play audio
    - Check volume is not muted
    - Test with headphones if speakers don't work

**Prevention**:
- Always grant microphone permission when prompted
- Keep recordings short (under 30 seconds) for faster processing
- Monitor backend logs for 🎤 and ✅ emoji indicators

#### ❌ Audio Playback Issues

**Symptoms**:
- Voice processing succeeds but no audio plays
- "Failed to play audio response" error
- Audio plays but is distorted or choppy
- Volume is too low or too high

**Root Causes**:
- Browser audio blocked
- ElevenLabs API issues
- Audio format not supported
- Network issues downloading audio

**Solutions**:

1. ✅ **Check browser audio settings**
   - Ensure site is not muted
   - Check browser volume mixer
   - Try clicking page first (some browsers require user interaction)

2. ✅ **Verify ElevenLabs API**
   ```bash
   # Test ElevenLabs API:
   curl https://api.elevenlabs.io/v1/voices \
     -H "xi-api-key: $ELEVENLABS_API_KEY"
   ```

3. ✅ **Check backend logs**
   - Look for 🔊 emoji (audio generation)
   - Look for ✅ emoji (success)
   - Check for API errors

4. ✅ **Test with different voice**
   - Try different `ELEVENLABS_VOICE_ID` in `.env`
   - List available voices at: https://elevenlabs.io/app/voice-library

5. ✅ **Check network tab**
   - Open DevTools (F12) → Network tab
   - Look for audio file downloads
   - Check for 200 status codes

**Prevention**:
- Ensure ElevenLabs API key has sufficient credits
- Test audio playback with simple "Hello" message first

---

### 📦 Dependency Issues

#### ❌ "Module not found" / Import Errors

**Symptoms**:
- Python import errors
- `ModuleNotFoundError` in backend
- TypeScript import errors in frontend
- Missing package errors

**Root Causes**:
- Dependencies not installed
- Virtual environment not activated
- Package version conflicts
- Corrupted node_modules

**Solutions**:

1. ✅ **Reinstall Python dependencies**
   ```bash
   # Clean install
   rm -rf .venv
   uv sync
   ```

2. ✅ **Reinstall frontend dependencies**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   cd ..
   ```

3. ✅ **Verify virtual environment**
   ```bash
   # Check if .venv is activated
   which python  # Should show .venv path
   
   # Activate if needed
   # Windows:
   .venv\Scripts\activate
   
   # Linux/Mac:
   source .venv/bin/activate
   ```

4. ✅ **Check Python version**
   ```bash
   python --version  # Should be 3.12+
   ```

5. ✅ **Check Node version**
   ```bash
   node --version  # Should be 18+
   npm --version
   ```

**Prevention**:
- Always use `uv sync` after pulling new code
- Run `npm install` after pulling frontend changes

---

### 🔧 Port Conflicts

#### ❌ "Port already in use" / Address in Use

**Symptoms**:
- `OSError: [Errno 48] Address already in use`
- Server fails to start
- Port 8000 or 3000 occupied

**Root Causes**:
- Previous server still running
- Another application using the port
- Zombie process holding port

**Solutions**:

1. ✅ **Find process using port**
   ```bash
   # Windows:
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   
   # Linux/Mac:
   lsof -ti:8000 | xargs kill -9
   lsof -ti:3000 | xargs kill -9
   ```

2. ✅ **Use different port**
   ```bash
   # Backend on different port:
   uvicorn ai_companion.interfaces.web.app:app --port 8001
   
   # Update frontend/.env:
   VITE_API_BASE_URL=http://localhost:8001/api/v1
   ```

3. ✅ **Restart computer**
   - Last resort if processes won't die

**Prevention**:
- Always stop servers with Ctrl+C (not closing terminal)
- Use `python scripts/run_dev_server.py` which handles cleanup

---

### 🗄️ Database Issues

#### ❌ Memory/Qdrant Connection Issues

**Symptoms**:
- "Cannot connect to Qdrant" errors
- Memory operations fail
- Timeout connecting to vector database

**Root Causes**:
- Qdrant credentials incorrect
- Qdrant service down
- Network connectivity issues
- Local Qdrant not running

**Solutions**:

1. ✅ **Check Qdrant credentials**
   ```bash
   # Verify .env contains:
   QDRANT_URL=https://your-cluster.qdrant.io
   QDRANT_API_KEY=your_api_key
   ```

2. ✅ **Test Qdrant connection**
   ```bash
   curl $QDRANT_URL/collections \
     -H "api-key: $QDRANT_API_KEY"
   ```

3. ✅ **Use local Qdrant for development**
   ```bash
   # Run Qdrant locally with Docker:
   docker run -p 6333:6333 qdrant/qdrant
   
   # Update .env:
   QDRANT_URL=http://localhost:6333
   QDRANT_API_KEY=  # Leave empty for local
   ```

4. ✅ **Check Qdrant service status**
   - Visit Qdrant Cloud dashboard
   - Verify cluster is running
   - Check for maintenance windows

**Prevention**:
- Use local Qdrant for development
- Monitor Qdrant service status

---

### 🚨 General Debugging Tips

#### Enable Debug Logging

```bash
# Add to .env:
LOG_LEVEL=DEBUG
```

#### Check All Logs

- **Backend logs**: Terminal running backend server
- **Frontend logs**: Browser console (F12)
- **Network logs**: Browser DevTools → Network tab

#### Look for Emoji Indicators

- 🚀 = Startup
- ✅ = Success
- ❌ = Error
- 🔌 = Connection
- 🎨 = Frontend/Assets
- 🎤 = Voice processing
- 🔊 = Audio generation
- 📊 = Metrics

#### Common Error Patterns

| Error Message | Likely Cause | Quick Fix |
|--------------|--------------|-----------|
| `ERR_CONNECTION_REFUSED` | Backend not running | Start backend server |
| `404 Not Found` | Asset not built | Run `npm run build` |
| `CORS error` | CORS misconfigured | Check `DEV_ALLOWED_ORIGINS` |
| `Microphone denied` | Permission not granted | Allow in browser settings |
| `Module not found` | Dependencies missing | Run `uv sync` or `npm install` |
| `Port in use` | Process already running | Kill process or use different port |

#### Still Stuck?

1. ✅ Check all environment variables are set correctly
2. ✅ Restart both frontend and backend servers
3. ✅ Clear browser cache and cookies
4. ✅ Try in incognito/private mode
5. ✅ Check GitHub issues for similar problems
6. ✅ Review recent code changes
7. ✅ Ask for help with specific error messages and logs

## Performance Optimization

### Backend Performance

- Use `llama-3.1-8b-instant` for non-critical tasks
- Adjust `WORKFLOW_TIMEOUT_SECONDS` based on your needs
- Monitor Groq API usage and rate limits

### Frontend Performance

- Assets are cached for 1 year in production
- 3D models are loaded progressively
- Audio is streamed, not downloaded entirely

### Memory Management

- Conversations are summarized after N messages
- Old audio files are cleaned up automatically
- Vector database is optimized for fast retrieval

## Testing Checklist

This section provides comprehensive testing procedures to verify that Rose is working correctly before deployment.

### 🧪 Manual Testing Checklist

Use this checklist to manually verify all features are working correctly.

#### Development Mode Testing

- [ ] **1. Server Startup**
  - [ ] Run `python scripts/run_dev_server.py`
  - [ ] Verify backend starts on port 8000 (look for 🔌 emoji)
  - [ ] Verify frontend starts on port 3000 (look for 🎨 emoji)
  - [ ] Check terminal shows "✅ Development servers running!"
  - [ ] Verify URLs are displayed correctly

- [ ] **2. Frontend Loading**
  - [ ] Open http://localhost:3000 in browser
  - [ ] Verify page loads without errors
  - [ ] Check browser console (F12) for errors
  - [ ] Verify loading screen appears
  - [ ] Verify loading progress updates (0% → 100%)
  - [ ] Verify 3D scene renders correctly
  - [ ] Check all styles are applied (not plain HTML)

- [ ] **3. Health Check**
  - [ ] Verify health check runs on app startup (look for 🏥 emoji in console)
  - [ ] Check health check passes (look for ✅ emoji)
  - [ ] Test with backend stopped: should show connection error
  - [ ] Restart backend: error should clear

- [ ] **4. Asset Loading**
  - [ ] Verify CSS loads (check for 🎨 emoji in console)
  - [ ] Verify 3D models load (check for 🎭 emoji in console)
  - [ ] Verify audio assets load (check for 🎵 emoji in console)
  - [ ] Check loading screen shows asset names
  - [ ] Verify no 404 errors in Network tab
  - [ ] Confirm all assets show "✅ loaded successfully"

- [ ] **5. Voice Interaction**
  - [ ] Click voice button (microphone icon)
  - [ ] Grant microphone permission when prompted
  - [ ] Verify recording indicator appears
  - [ ] Speak a test message (e.g., "Hello Rose")
  - [ ] Verify recording stops after speaking
  - [ ] Check backend logs for 🎤 emoji (voice processing start)
  - [ ] Verify transcription completes (look for ✅ emoji)
  - [ ] Verify audio response plays automatically
  - [ ] Check audio quality and volume
  - [ ] Verify 3D avatar animates during speech

- [ ] **6. Error Handling**
  - [ ] **Backend Unreachable**: Stop backend, try voice interaction
    - [ ] Should show "Cannot connect to Rose" error
    - [ ] Error should have ❌ emoji
    - [ ] Error should auto-dismiss after 5 seconds
  - [ ] **Microphone Denied**: Deny microphone permission
    - [ ] Should show "Microphone access denied" error
    - [ ] Error should include instructions to fix
  - [ ] **Invalid Audio**: Send empty/corrupted audio
    - [ ] Should show user-friendly error message
    - [ ] Should not crash the application

- [ ] **7. Hot Reload (Development)**
  - [ ] Edit a Python file in `src/ai_companion/`
  - [ ] Save file
  - [ ] Verify backend reloads automatically (check terminal)
  - [ ] Edit a TypeScript file in `frontend/src/`
  - [ ] Save file
  - [ ] Verify frontend hot-reloads in browser (no manual refresh)

- [ ] **8. API Documentation**
  - [ ] Open http://localhost:8000/api/v1/docs
  - [ ] Verify Swagger UI loads
  - [ ] Check all endpoints are documented
  - [ ] Test `/api/v1/health` endpoint
  - [ ] Verify response format matches documentation

#### Production Mode Testing

- [ ] **9. Production Build**
  - [ ] Run `python scripts/build_and_serve.py`
  - [ ] Verify frontend build starts (look for 🎨 emoji)
  - [ ] Check for "✅ Build complete!" message
  - [ ] Verify build output in `src/ai_companion/interfaces/web/static/`
  - [ ] Check `index.html` exists
  - [ ] Check `assets/` directory exists with JS/CSS files
  - [ ] Verify no build errors or warnings

- [ ] **10. Production Server**
  - [ ] Verify server starts on port 8000 (look for 🚀 emoji)
  - [ ] Open http://localhost:8000 in browser
  - [ ] Verify page loads from FastAPI (not Vite)
  - [ ] Check Network tab: assets served from `/assets/`
  - [ ] Verify cache headers on static assets (1 year)
  - [ ] Verify HTML cache headers (5 minutes)

- [ ] **11. Production Features**
  - [ ] Verify all CSS styles applied correctly
  - [ ] Verify 3D scene renders properly
  - [ ] Test voice interaction end-to-end
  - [ ] Check audio playback works
  - [ ] Verify error handling works
  - [ ] Test in multiple browsers (Chrome, Firefox, Safari, Edge)
  - [ ] Test on mobile device (responsive design)

- [ ] **12. Performance**
  - [ ] Check page load time (should be < 3 seconds)
  - [ ] Verify 3D scene runs at 60 FPS on desktop
  - [ ] Verify 3D scene runs at 30 FPS on mobile
  - [ ] Check voice processing latency (should be < 5 seconds)
  - [ ] Monitor memory usage (should not grow unbounded)
  - [ ] Test with slow network (throttle in DevTools)

#### Configuration Testing

- [ ] **13. Environment Variables**
  - [ ] Verify all required variables in `.env`
  - [ ] Test with missing `GROQ_API_KEY`: should fail gracefully
  - [ ] Test with invalid API key: should show clear error
  - [ ] Verify `VITE_API_BASE_URL` in `frontend/.env`
  - [ ] Test with wrong API URL: should show connection error

- [ ] **14. Configuration Constants**
  - [ ] Verify no hardcoded ports in code (use `server_config.py`)
  - [ ] Verify no hardcoded timeouts (use constants)
  - [ ] Verify no hardcoded file sizes (use constants)
  - [ ] Check all constants have emoji documentation
  - [ ] Verify constants are imported correctly

#### Logging and Observability

- [ ] **15. Emoji Logging**
  - [ ] Verify all logs have emoji indicators
  - [ ] Check 🚀 for startup events
  - [ ] Check ✅ for success events
  - [ ] Check ❌ for error events
  - [ ] Check 🔌 for connection events
  - [ ] Check 🎨 for frontend/asset events
  - [ ] Check 🎤 for voice processing events
  - [ ] Check 🔊 for audio generation events
  - [ ] Verify logs are easy to scan visually

- [ ] **16. Error Messages**
  - [ ] Verify all error messages are user-friendly
  - [ ] Check errors include actionable guidance
  - [ ] Verify errors use constants from `errorMessages.ts`
  - [ ] Test error auto-dismiss (5 seconds for transient errors)
  - [ ] Verify critical errors stay visible until dismissed

### 🤖 Automated Testing

Run automated tests to verify code quality and functionality.

#### Backend Tests

```bash
# Run all backend tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src --cov-report=html --cov-report=term

# Run specific test categories
uv run pytest tests/unit/                          # Unit tests only
uv run pytest tests/integration/                   # Integration tests only
uv run pytest tests/test_voice_interaction.py      # Voice tests
uv run pytest tests/test_performance_benchmarks.py # Performance tests

# Run with verbose output
uv run pytest -v

# Run specific test
uv run pytest tests/unit/test_memory.py::test_memory_extraction -v
```

**Expected Results**:
- All tests should pass (green)
- Coverage should be > 70%
- No warnings or deprecation notices

#### Frontend Tests

```bash
cd frontend

# Run all frontend tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode (for development)
npm run test:watch

# Run specific test file
npm test -- useVoiceInteraction.test.ts

# Run with verbose output
npm test -- --verbose
```

**Expected Results**:
- All tests should pass
- Coverage should be > 60%
- No console errors or warnings

#### Type Checking

```bash
# Backend type checking
uv run mypy src/

# Frontend type checking
cd frontend
npm run type-check
```

**Expected Results**:
- No type errors
- All type hints valid

#### Linting and Formatting

```bash
# Backend linting
make lint-check

# Backend formatting
make format-check

# Fix linting issues
make lint-fix

# Fix formatting issues
make format-fix

# Frontend linting
cd frontend
npm run lint

# Frontend formatting
npm run format
```

**Expected Results**:
- No linting errors
- Code follows style guide
- All imports sorted correctly

#### Integration Tests

```bash
# Run end-to-end integration tests
uv run pytest tests/integration/ -v

# Run with real API calls (requires API keys)
uv run pytest tests/integration/ --run-integration -v
```

**Expected Results**:
- All integration tests pass
- API calls succeed
- Workflow completes end-to-end

#### Performance Tests

```bash
# Run performance benchmarks
uv run pytest tests/test_performance_benchmarks.py -v

# Run with profiling
uv run python scripts/profile_performance.py
```

**Expected Results**:
- Response times within acceptable limits
- Memory usage stable
- No memory leaks

### 📋 Pre-Deployment Checklist

Complete this checklist before deploying to production.

#### Code Quality

- [ ] All tests passing (backend and frontend)
- [ ] Code coverage > 70% (backend) and > 60% (frontend)
- [ ] No linting errors
- [ ] No type checking errors
- [ ] All code formatted correctly
- [ ] No hardcoded secrets or API keys in code
- [ ] All magic numbers replaced with named constants

#### Configuration

- [ ] All environment variables documented
- [ ] `.env.example` up to date
- [ ] `frontend/.env.example` up to date
- [ ] Production environment variables set
- [ ] API keys valid and have sufficient credits
- [ ] CORS origins configured for production domain
- [ ] Rate limiting enabled
- [ ] Security headers enabled

#### Documentation

- [ ] README.md up to date
- [ ] DEVELOPMENT.md complete
- [ ] API documentation accurate
- [ ] Deployment guide reviewed
- [ ] Troubleshooting section complete
- [ ] All new features documented

#### Security

- [ ] No secrets in version control
- [ ] API keys rotated if exposed
- [ ] HTTPS enabled in production
- [ ] CORS properly configured
- [ ] Rate limiting tested
- [ ] Input validation in place
- [ ] Error messages don't leak sensitive info

#### Performance

- [ ] Frontend build optimized (minified, tree-shaken)
- [ ] Static assets cached properly
- [ ] API response times acceptable
- [ ] Memory usage stable
- [ ] No memory leaks detected
- [ ] Database queries optimized

#### Monitoring

- [ ] Health check endpoint working
- [ ] Logging configured correctly
- [ ] Error tracking enabled (Sentry, etc.)
- [ ] Metrics collection working
- [ ] Alerts configured
- [ ] Backup strategy in place

#### Testing

- [ ] Manual testing checklist completed
- [ ] Automated tests passing
- [ ] Tested in multiple browsers
- [ ] Tested on mobile devices
- [ ] Tested with slow network
- [ ] Error scenarios tested
- [ ] Load testing completed (if applicable)

### 🚀 Deployment Commands

Once all tests pass and the pre-deployment checklist is complete, use these commands to deploy.

#### Build for Production

```bash
# Build frontend
cd frontend
npm run build
cd ..

# Verify build output
ls -la src/ai_companion/interfaces/web/static/
```

#### Test Production Build Locally

```bash
# Run production server locally
python scripts/build_and_serve.py

# Test at http://localhost:8000
# Complete manual testing checklist
```

#### Deploy to Railway (Example)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Link to project
railway link

# Deploy
railway up

# Check deployment status
railway status

# View logs
railway logs
```

#### Deploy to Other Platforms

See platform-specific guides:
- **Railway**: [docs/RAILWAY_SETUP.md](docs/RAILWAY_SETUP.md)
- **Google Cloud Run**: [docs/gcp_setup.md](docs/gcp_setup.md)
- **Docker**: [docker/README.md](docker/README.md)
- **General**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

#### Post-Deployment Verification

After deploying, verify the production deployment:

- [ ] Visit production URL
- [ ] Verify health check: `https://your-domain.com/api/v1/health`
- [ ] Test voice interaction end-to-end
- [ ] Check error handling works
- [ ] Verify logs are being collected
- [ ] Test from different locations/networks
- [ ] Monitor for errors in first 24 hours

### 📊 Testing Best Practices

#### When to Run Tests

- **Before every commit**: Run linting and formatting
- **Before every PR**: Run full test suite
- **Before deployment**: Complete full manual + automated testing
- **After deployment**: Run smoke tests in production

#### Writing New Tests

When adding new features:

1. Write tests first (TDD approach)
2. Test happy path and error cases
3. Keep tests focused and minimal
4. Use descriptive test names
5. Mock external API calls
6. Test edge cases
7. Update this checklist if needed

#### Debugging Failed Tests

If tests fail:

1. Read the error message carefully
2. Check recent code changes
3. Run test in isolation: `pytest tests/path/to/test.py::test_name -v`
4. Add debug logging
5. Use debugger: `pytest --pdb`
6. Check environment variables
7. Verify dependencies are up to date

---

## 🚀 Deployment

### Deployment Quick Reference

This section provides a quick reference for deploying Rose to production. For comprehensive deployment documentation, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

#### Pre-Deployment Checklist

Before deploying, ensure:
- [ ] All tests pass (`uv run pytest` and `cd frontend && npm test`)
- [ ] Frontend builds successfully (`cd frontend && npm run build`)
- [ ] All required environment variables are documented
- [ ] API keys are valid and have sufficient credits
- [ ] Production environment variables are set
- [ ] CORS origins configured for production domain
- [ ] Security headers enabled (`ENABLE_SECURITY_HEADERS=true`)
- [ ] Rate limiting enabled (`RATE_LIMIT_ENABLED=true`)

#### Quick Deploy Commands

**Local Production Test:**
```bash
python scripts/build_and_serve.py
# Test at http://localhost:8000
```

**Railway:**
```bash
railway login
railway link
railway up
```

**Render:**
- Connect GitHub repo in dashboard
- Build: `cd frontend && npm install && npm run build && cd .. && uv sync`
- Start: `uvicorn ai_companion.interfaces.web.app:app --host 0.0.0.0 --port $PORT`

**Docker:**
```bash
docker build -t rose-healer .
docker run -p 8000:8000 --env-file .env rose-healer
```

### Production Build Process

Before deploying to production, ensure you build the frontend correctly:

```bash
# Build frontend for production
cd frontend
npm run build
cd ..

# Verify build output
ls -la src/ai_companion/interfaces/web/static/
# Should contain: index.html, assets/ directory
```

The build process:
1. 🎨 Compiles TypeScript to JavaScript
2. 📦 Bundles and minifies all assets
3. 🗜️ Optimizes images and 3D models
4. 📁 Outputs to `src/ai_companion/interfaces/web/static/`
5. ✅ Generates cache-friendly filenames with hashes

**Build Configuration:**
- Output directory: `src/ai_companion/interfaces/web/static/`
- Configured in: `frontend/vite.config.ts`
- Build command: `npm run build` (in frontend directory)
- Build time: ~30-60 seconds depending on system

**Verifying Build Success:**
```bash
# Check build output exists
ls -la src/ai_companion/interfaces/web/static/

# Should see:
# - index.html (main HTML file)
# - assets/ (directory with JS, CSS, fonts, 3D models)
# - vite.svg (favicon)

# Check build size
du -sh src/ai_companion/interfaces/web/static/
# Should be ~5-15MB depending on assets
```

### Environment Variable Requirements

#### Required for All Deployments

```bash
# API Keys (REQUIRED)
GROQ_API_KEY=gsk_your_production_key
ELEVENLABS_API_KEY=your_production_key
ELEVENLABS_VOICE_ID=your_production_voice_id
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_production_key

# Server Configuration
PORT=8000                    # Platform may override this
HOST=0.0.0.0                # Listen on all interfaces
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Security
RATE_LIMIT_ENABLED=true
ENABLE_SECURITY_HEADERS=true

# Logging
LOG_LEVEL=INFO              # Use INFO or WARNING in production
LOG_FORMAT=json             # Structured logging for aggregation
```

#### Optional but Recommended

```bash
# Monitoring (Highly Recommended)
SENTRY_DSN=https://your-sentry-dsn
ENVIRONMENT=production
APP_VERSION=1.0.0

# Performance
FEATURE_TTS_CACHE_ENABLED=true
TTS_CACHE_TTL_HOURS=24

# Resource Management
SESSION_RETENTION_DAYS=7
AUDIO_CLEANUP_MAX_AGE_HOURS=24
```

### Platform-Specific Deployment

#### Railway

Railway automatically detects the Python application and builds the frontend.

**Setup:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create new project or link existing
railway init  # or railway link

# Set environment variables
railway variables set GROQ_API_KEY=your_key
railway variables set ELEVENLABS_API_KEY=your_key
# ... set all required variables

# Deploy
railway up
```

**Important Railway Notes:**
- Railway automatically sets `PORT` environment variable
- Use `PORT` from environment, not hardcoded 8000
- Frontend build happens automatically during deployment
- Check `config/railway.json` for build configuration

**Verify Deployment:**
```bash
# Check deployment status
railway status

# View logs
railway logs

# Open in browser
railway open
```

#### Render

**Setup:**
1. Connect your GitHub repository
2. Create new Web Service
3. Configure build command: `cd frontend && npm install && npm run build && cd .. && uv sync`
4. Configure start command: `uvicorn ai_companion.interfaces.web.app:app --host 0.0.0.0 --port $PORT`
5. Add environment variables in Render dashboard

#### Fly.io

**Setup:**
```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Launch app
flyctl launch

# Set secrets
flyctl secrets set GROQ_API_KEY=your_key
flyctl secrets set ELEVENLABS_API_KEY=your_key
# ... set all required secrets

# Deploy
flyctl deploy
```

#### Docker Deployment

**Build and run with Docker:**
```bash
# Build image
docker build -t rose-healer .

# Run container
docker run -p 8000:8000 \
  -e GROQ_API_KEY=your_key \
  -e ELEVENLABS_API_KEY=your_key \
  -e ELEVENLABS_VOICE_ID=your_voice \
  -e QDRANT_URL=your_qdrant_url \
  -e QDRANT_API_KEY=your_qdrant_key \
  rose-healer
```

**Using Docker Compose:**
```bash
# Create .env file with all variables
cp .env.example .env
# Edit .env with production values

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Common Deployment Issues

#### ❌ Frontend Not Loading / 404 Errors

**Symptoms:**
- Production site shows blank page
- Browser console shows 404 for assets
- `/assets/` files not found

**Solutions:**

1. ✅ **Verify frontend was built**
   ```bash
   # Check build output exists
   ls -la src/ai_companion/interfaces/web/static/
   # Should contain index.html and assets/ directory
   ```

2. ✅ **Rebuild frontend**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   cd ..
   ```

3. ✅ **Check Vite output directory**
   - Verify `frontend/vite.config.ts` has:
     ```typescript
     outDir: path.resolve(__dirname, '../src/ai_companion/interfaces/web/static')
     ```

4. ✅ **Verify static file serving**
   - Check `src/ai_companion/interfaces/web/app.py` mounts static files correctly
   - Ensure `FRONTEND_BUILD_DIR` constant points to correct path

#### ❌ Environment Variables Not Loading

**Symptoms:**
- App crashes on startup
- "Missing required environment variable" errors
- API keys not found

**Solutions:**

1. ✅ **Verify all required variables are set**
   ```bash
   # Check which variables are missing
   python -c "from ai_companion.settings import settings; print('✅ Config valid')"
   ```

2. ✅ **Platform-specific variable setting**
   - **Railway**: Use `railway variables set KEY=value`
   - **Render**: Set in dashboard under "Environment"
   - **Fly.io**: Use `flyctl secrets set KEY=value`
   - **Docker**: Pass via `-e` flag or `.env` file

3. ✅ **Check variable names match exactly**
   - Variable names are case-sensitive
   - No spaces around `=` in `.env` files
   - No quotes needed in most platforms

#### ❌ CORS Errors in Production

**Symptoms:**
- Frontend can't connect to API
- Browser console shows CORS errors
- "Access-Control-Allow-Origin" errors

**Solutions:**

1. ✅ **Set ALLOWED_ORIGINS correctly**
   ```bash
   # Include your production domain
   ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

2. ✅ **Don't use wildcards in production**
   ```bash
   # ❌ Bad (security risk)
   ALLOWED_ORIGINS=*
   
   # ✅ Good (specific domains)
   ALLOWED_ORIGINS=https://yourdomain.com
   ```

3. ✅ **Match protocol (http vs https)**
   - Production should use `https://`
   - Development uses `http://`

#### ❌ Voice Processing Fails in Production

**Symptoms:**
- Voice button doesn't work
- "Voice processing error" messages
- Microphone permission issues

**Solutions:**

1. ✅ **Verify HTTPS is enabled**
   - Browser requires HTTPS for microphone access
   - Use platform's automatic HTTPS (Railway, Render, Fly.io all provide this)

2. ✅ **Check API keys are valid**
   ```bash
   # Test Groq API key
   curl https://api.groq.com/openai/v1/models \
     -H "Authorization: Bearer $GROQ_API_KEY"
   
   # Test ElevenLabs API key
   curl https://api.elevenlabs.io/v1/voices \
     -H "xi-api-key: $ELEVENLABS_API_KEY"
   ```

3. ✅ **Verify Qdrant connection**
   ```bash
   # Check Qdrant is accessible
   curl $QDRANT_URL/collections \
     -H "api-key: $QDRANT_API_KEY"
   ```

4. ✅ **Check file size limits**
   - Ensure `MAX_AUDIO_FILE_SIZE_MB` is appropriate
   - Platform may have request size limits

#### ❌ Memory or Performance Issues

**Symptoms:**
- App crashes with out-of-memory errors
- Slow response times
- High CPU usage

**Solutions:**

1. ✅ **Enable TTS caching**
   ```bash
   FEATURE_TTS_CACHE_ENABLED=true
   TTS_CACHE_TTL_HOURS=24
   ```

2. ✅ **Configure resource limits**
   ```bash
   # Limit memory usage
   MAX_REQUEST_SIZE=10485760  # 10MB
   SESSION_RETENTION_DAYS=7
   AUDIO_CLEANUP_MAX_AGE_HOURS=24
   ```

3. ✅ **Adjust workflow timeouts**
   ```bash
   # Reduce timeouts if needed
   WORKFLOW_TIMEOUT_SECONDS=45
   API_REQUEST_TIMEOUT_SECONDS=50
   ```

4. ✅ **Scale up instance size**
   - Railway: Upgrade to larger plan
   - Render: Increase instance size
   - Fly.io: Scale VM size

### Post-Deployment Checklist

After deploying, verify everything works:

- [ ] ✅ Visit production URL - site loads
- [ ] ✅ Health check passes: `https://your-domain.com/api/v1/health`
- [ ] ✅ Frontend loads without errors (check browser console)
- [ ] ✅ All CSS and 3D assets load correctly
- [ ] ✅ Voice button appears and is clickable
- [ ] ✅ Microphone permission request works
- [ ] ✅ Voice recording works end-to-end
- [ ] ✅ Audio response plays correctly
- [ ] ✅ Error messages display properly
- [ ] ✅ Test from different browsers (Chrome, Firefox, Safari)
- [ ] ✅ Test from mobile device
- [ ] ✅ Check logs for errors
- [ ] ✅ Verify monitoring/Sentry is receiving data
- [ ] ✅ Test rate limiting works
- [ ] ✅ Verify CORS is configured correctly

### Deployment Troubleshooting Guide

This section covers common issues specific to production deployments.

#### Build Failures

**❌ Frontend Build Fails During Deployment**

**Symptoms:**
- Deployment fails at build step
- "npm run build" errors in logs
- TypeScript compilation errors
- Out of memory during build

**Solutions:**

1. ✅ **Check Node.js version**
   ```bash
   # Ensure Node 18+ is available
   node --version
   ```
   - Most platforms auto-detect from `.nvmrc` or `package.json`
   - Railway/Render: Specify in build settings if needed

2. ✅ **Verify package.json scripts**
   ```json
   {
     "scripts": {
       "build": "vite build",
       "type-check": "tsc --noEmit"
     }
   }
   ```

3. ✅ **Check for TypeScript errors locally**
   ```bash
   cd frontend
   npm run type-check
   npm run build
   ```

4. ✅ **Increase build memory (if OOM)**
   - Railway: Upgrade plan for more memory
   - Render: Increase instance size
   - Docker: Add `--memory` flag

5. ✅ **Check build logs for specific errors**
   - Look for file path errors
   - Check for missing dependencies
   - Verify all imports are correct

**❌ Python Dependencies Fail to Install**

**Symptoms:**
- `uv sync` fails during deployment
- Missing system dependencies
- Compilation errors for native extensions

**Solutions:**

1. ✅ **Verify pyproject.toml is valid**
   ```bash
   # Test locally
   uv sync --frozen
   ```

2. ✅ **Check for system dependencies**
   - Some packages need build tools (gcc, g++)
   - Dockerfile includes these: `apt-get install build-essential`

3. ✅ **Use frozen lockfile**
   ```bash
   # In deployment config
   uv sync --frozen
   ```

4. ✅ **Check Python version**
   - Requires Python 3.12+
   - Verify platform supports this version

#### Runtime Failures

**❌ Application Crashes on Startup**

**Symptoms:**
- Service starts but immediately crashes
- Health check fails
- "Application error" page

**Solutions:**

1. ✅ **Check environment variables**
   ```bash
   # Verify all required variables are set
   # Required: GROQ_API_KEY, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID,
   #           QDRANT_URL, QDRANT_API_KEY
   ```

2. ✅ **Review startup logs**
   - Look for ❌ emoji indicators
   - Check for "Missing required environment variable" errors
   - Verify API key validation passes

3. ✅ **Test configuration locally**
   ```bash
   # Use production environment variables locally
   python -c "from ai_companion.settings import settings; print('✅ Config valid')"
   ```

4. ✅ **Check external service connectivity**
   ```bash
   # Test Groq API
   curl https://api.groq.com/openai/v1/models \
     -H "Authorization: Bearer $GROQ_API_KEY"
   
   # Test Qdrant
   curl $QDRANT_URL/collections \
     -H "api-key: $QDRANT_API_KEY"
   ```

5. ✅ **Verify port configuration**
   - Use `PORT` environment variable (set by platform)
   - Don't hardcode port 8000 in production

**❌ Static Files Not Serving (404 Errors)**

**Symptoms:**
- Homepage loads but shows blank page
- Browser console shows 404 for `/assets/*` files
- CSS and JavaScript not loading

**Solutions:**

1. ✅ **Verify frontend was built during deployment**
   ```bash
   # Check deployment logs for:
   # "🎨 Starting frontend build..."
   # "✅ Build complete!"
   ```

2. ✅ **Check build output location**
   - Should be: `src/ai_companion/interfaces/web/static/`
   - Verify in deployment logs or SSH into container

3. ✅ **Verify Vite config output path**
   ```typescript
   // frontend/vite.config.ts
   build: {
     outDir: path.resolve(__dirname, '../src/ai_companion/interfaces/web/static'),
     emptyOutDir: true,
   }
   ```

4. ✅ **Check FastAPI static file mounting**
   ```python
   # src/ai_companion/interfaces/web/app.py
   # Should see log: "✅ Frontend build found"
   # If "❌ Frontend build not found", rebuild is needed
   ```

5. ✅ **Verify file permissions**
   - Ensure static files are readable by application user
   - Check Dockerfile sets correct permissions

**❌ HTTPS/SSL Issues**

**Symptoms:**
- "Not secure" warning in browser
- Mixed content errors
- Microphone doesn't work (requires HTTPS)

**Solutions:**

1. ✅ **Enable platform HTTPS**
   - Railway: Automatic with custom domain
   - Render: Automatic for all deployments
   - Fly.io: Automatic with certificates

2. ✅ **Configure custom domain**
   - Add domain in platform dashboard
   - Update DNS records (CNAME or A record)
   - Wait for SSL certificate provisioning (5-30 minutes)

3. ✅ **Update ALLOWED_ORIGINS**
   ```bash
   # Use HTTPS in production
   ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

4. ✅ **Force HTTPS redirect**
   - Most platforms handle this automatically
   - Verify in platform settings

#### Performance Issues

**❌ Slow Response Times**

**Symptoms:**
- API requests take > 5 seconds
- Voice processing times out
- Users experience lag

**Solutions:**

1. ✅ **Enable TTS caching**
   ```bash
   FEATURE_TTS_CACHE_ENABLED=true
   TTS_CACHE_TTL_HOURS=24
   ```

2. ✅ **Check external API latency**
   - Groq API response time
   - ElevenLabs TTS generation time
   - Qdrant query performance

3. ✅ **Optimize workflow timeouts**
   ```bash
   # Reduce if needed
   WORKFLOW_TIMEOUT_SECONDS=45
   API_REQUEST_TIMEOUT_SECONDS=50
   ```

4. ✅ **Scale up resources**
   - Increase instance size
   - Add more workers (Railway config)
   - Consider CDN for static assets

5. ✅ **Monitor resource usage**
   - Check CPU usage
   - Check memory usage
   - Look for memory leaks

**❌ High Memory Usage / OOM Kills**

**Symptoms:**
- Application crashes randomly
- "Out of memory" errors
- Platform restarts service frequently

**Solutions:**

1. ✅ **Reduce memory footprint**
   ```bash
   # Limit session retention
   SESSION_RETENTION_DAYS=3
   
   # Reduce memory retrieval
   MEMORY_TOP_K=2
   
   # Enable cleanup
   AUDIO_CLEANUP_MAX_AGE_HOURS=12
   ```

2. ✅ **Optimize worker count**
   ```json
   // config/railway.json
   {
     "deploy": {
       "startCommand": "uvicorn ... --workers 2"  // Reduce workers
     }
   }
   ```

3. ✅ **Upgrade instance size**
   - Railway: Upgrade to Developer or Pro plan
   - Render: Increase instance size
   - Fly.io: Scale VM memory

4. ✅ **Monitor memory leaks**
   ```bash
   # Check for growing memory usage
   # Review logs for memory warnings
   ```

#### API Integration Issues

**❌ Groq API Errors**

**Symptoms:**
- Voice transcription fails
- "Groq API error" messages
- Rate limit errors

**Solutions:**

1. ✅ **Verify API key**
   ```bash
   curl https://api.groq.com/openai/v1/models \
     -H "Authorization: Bearer $GROQ_API_KEY"
   ```

2. ✅ **Check rate limits**
   - Free tier: Limited requests per minute
   - Upgrade to paid plan if needed
   - Implement request queuing

3. ✅ **Monitor API status**
   - Check Groq status page
   - Look for service outages
   - Have fallback strategy

4. ✅ **Adjust timeouts**
   ```bash
   LLM_TIMEOUT_SECONDS=45
   STT_TIMEOUT=90
   ```

**❌ ElevenLabs TTS Failures**

**Symptoms:**
- Audio generation fails
- "ElevenLabs API error" messages
- No audio playback

**Solutions:**

1. ✅ **Verify API key and credits**
   ```bash
   curl https://api.elevenlabs.io/v1/user \
     -H "xi-api-key: $ELEVENLABS_API_KEY"
   ```

2. ✅ **Check voice ID**
   ```bash
   # List available voices
   curl https://api.elevenlabs.io/v1/voices \
     -H "xi-api-key: $ELEVENLABS_API_KEY"
   ```

3. ✅ **Enable caching**
   ```bash
   FEATURE_TTS_CACHE_ENABLED=true
   TTS_CACHE_TTL_HOURS=24
   ```

4. ✅ **Monitor quota usage**
   - Check character usage
   - Upgrade plan if needed
   - Implement usage tracking

**❌ Qdrant Connection Issues**

**Symptoms:**
- Memory operations fail
- "Cannot connect to Qdrant" errors
- Timeout errors

**Solutions:**

1. ✅ **Verify Qdrant credentials**
   ```bash
   curl $QDRANT_URL/collections \
     -H "api-key: $QDRANT_API_KEY"
   ```

2. ✅ **Check network connectivity**
   - Verify Qdrant cluster is running
   - Check firewall rules
   - Verify URL format (https://)

3. ✅ **Use Qdrant Cloud**
   - More reliable than self-hosted
   - Automatic backups
   - Better performance

4. ✅ **Configure timeouts**
   ```bash
   # Increase if needed
   QDRANT_TIMEOUT_SECONDS=30
   ```

#### Platform-Specific Issues

**Railway:**
- **Build timeout**: Upgrade plan or optimize build
- **Volume not persisting**: Configure volume in dashboard
- **Environment variables not loading**: Use `railway variables set`

**Render:**
- **Cold starts**: Upgrade from free tier
- **Build cache issues**: Clear build cache in dashboard
- **Static files not serving**: Check build command includes frontend build

**Fly.io:**
- **Region latency**: Deploy to region closer to users
- **Volume mounting**: Verify volume configuration in `fly.toml`
- **Secrets not loading**: Use `flyctl secrets set`

**Docker:**
- **Container exits immediately**: Check logs with `docker logs`
- **Port not accessible**: Verify port mapping `-p 8000:8000`
- **Environment variables**: Use `--env-file .env` or `-e` flags

### Getting Help with Deployment

If you encounter issues not covered here:

1. **Check platform status pages**
   - Railway: https://status.railway.app/
   - Render: https://status.render.com/
   - Fly.io: https://status.flyio.net/

2. **Review comprehensive guides**
   - [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Complete deployment guide
   - [docs/RAILWAY_SETUP.md](docs/RAILWAY_SETUP.md) - Railway-specific setup
   - [docs/OPERATIONS_RUNBOOK.md](docs/OPERATIONS_RUNBOOK.md) - Operations guide

3. **Check application logs**
   - Look for emoji indicators (❌ for errors)
   - Check startup sequence
   - Verify all services initialized

4. **Test locally first**
   ```bash
   # Test production build locally
   python scripts/build_and_serve.py
   ```

5. **Contact support**
   - Platform support (Railway, Render, Fly.io)
   - API provider support (Groq, ElevenLabs, Qdrant)
   - Open GitHub issue with logs and error details

### Monitoring Production

**Check application health:**
```bash
# Health endpoint
curl https://your-domain.com/api/v1/health

# Should return:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "timestamp": "2024-01-01T00:00:00Z"
# }
```

**View logs:**
- **Railway**: `railway logs`
- **Render**: View in dashboard
- **Fly.io**: `flyctl logs`
- **Docker**: `docker logs <container-id>`

**Monitor errors:**
- Set up Sentry for error tracking
- Check logs regularly for ❌ emoji indicators
- Monitor API response times
- Track memory and CPU usage

### Rollback Procedures

If deployment fails:

**Railway:**
```bash
# View deployments
railway deployments

# Rollback to previous
railway rollback <deployment-id>
```

**Render:**
- Use dashboard to rollback to previous deploy

**Fly.io:**
```bash
# List releases
flyctl releases

# Rollback
flyctl releases rollback <version>
```

**Docker:**
```bash
# Stop current container
docker stop <container-id>

# Start previous version
docker run <previous-image-tag>
```

### Deployment Best Practices

1. **Test locally first**
   - Always test production build locally: `python scripts/build_and_serve.py`
   - Verify all features work before deploying

2. **Use staging environment**
   - Deploy to staging first
   - Test thoroughly in staging
   - Then deploy to production

3. **Monitor after deployment**
   - Watch logs for first 30 minutes
   - Check error rates in Sentry
   - Test critical user flows

4. **Have rollback plan**
   - Know how to rollback quickly
   - Keep previous version accessible
   - Document rollback procedures

5. **Gradual rollout**
   - Deploy to small percentage of users first
   - Monitor for issues
   - Gradually increase traffic

For detailed deployment guides, see:
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - General deployment guide
- [docs/RAILWAY_SETUP.md](docs/RAILWAY_SETUP.md) - Railway-specific setup
- [docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md) - Complete checklist

## Additional Resources

- [README.md](README.md) - Project overview and quick start
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture
- [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) - API reference
- [tests/README.md](tests/README.md) - Testing guide

## Getting Help

- Check the [Troubleshooting](#troubleshooting) section above
- Review logs for emoji indicators (❌ for errors)
- Check browser console for frontend errors
- Review API documentation at http://localhost:8000/api/v1/docs

---

**Happy coding! 🚀**
