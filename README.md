# Rose the Healer Shaman 🌹

[![Tests](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/test.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/YOUR_USERNAME/YOUR_REPO/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/YOUR_REPO)

An AI grief counselor and holistic healing companion powered by open-source LLMs through Groq. Rose provides empathetic support using ancient healing wisdom through a voice-first web interface.

> **📖 New to Development?** Check out [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup instructions, troubleshooting, and configuration guides.

## 📋 Overview

Rose is a voice-first AI companion designed to provide therapeutic support for grief counseling and emotional healing. Built on LangGraph workflow orchestration, Rose combines modern AI technology with ancient healing wisdom to create a warm, grounding presence for users seeking emotional support.

### ✨ Key Features

- 🎤 **Voice-First Interaction**: Natural push-to-talk interface for hands-free conversations
- 💚 **Therapeutic Personality**: Empathetic healer shaman trained in ancient healing traditions
- 🧠 **Persistent Memory**: Remembers your journey across sessions using vector-based long-term memory
- ⚡ **Groq-Powered**: Fast, cost-effective inference using open-source models (Llama 3.3, Whisper)
- 🎨 **Beautiful UI**: React-based interface with smooth animations and visual feedback
- 🚀 **Easy Deployment**: Single-service architecture ready for Railway, Render, or Fly.io

## 🔧 Technology Stack

- **LangGraph**: Workflow orchestration and state management
- **Groq API**: LLM inference (Llama 3.3 70B) and speech-to-text (Whisper Large v3)
- **ElevenLabs**: Natural text-to-speech for Rose's calming voice
- **Qdrant**: Vector database for long-term memory
- **FastAPI**: Backend API server
- **React + TypeScript**: Frontend voice interface
- **Python 3.12+** with `uv` package manager

## 🚀 Quick Start

> **💡 Tip**: For detailed development instructions, troubleshooting, and configuration options, see **[DEVELOPMENT.md](DEVELOPMENT.md)**

### 📋 Prerequisites

- Python 3.12 or higher
- Node.js 18+ and npm (for frontend)
- `uv` package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- API keys for Groq, ElevenLabs, and Qdrant

### 📦 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-companion
   ```

2. **Install Python dependencies**
   ```bash
   uv sync
   ```

3. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

   Required variables:
   - `GROQ_API_KEY`: Get from [Groq Console](https://console.groq.com/)
   - `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID`: Get from [ElevenLabs](https://elevenlabs.io/)
   - `QDRANT_URL` and `QDRANT_API_KEY`: Get from [Qdrant Cloud](https://cloud.qdrant.io/)

### 🎮 Running Locally

#### 🚀 Development Mode (Recommended)

Start both frontend and backend with hot reload:

```bash
python scripts/run_dev_server.py
```

This starts:
- 🎨 Frontend dev server: http://localhost:3000 (with hot reload)
- 🔌 Backend API server: http://localhost:8000 (with auto-reload)
- 📚 API documentation: http://localhost:8000/api/v1/docs

Press Ctrl+C to stop both servers.

#### 📦 Production Mode

Build frontend and start production server:

```bash
python scripts/build_and_serve.py
```

This builds the frontend and serves it through FastAPI at http://localhost:8000

> **📖 Need Help?** See [DEVELOPMENT.md](DEVELOPMENT.md) for troubleshooting, configuration details, and advanced development workflows

## 💬 Usage

### 🎤 Voice Interaction

1. Click and hold the voice button to start recording
2. Speak your message while holding the button
3. Release to send your message to Rose
4. Rose will respond with both text and audio

### 🧠 Memory System

Rose remembers important details about your emotional journey:
- Personal information you share
- Emotional states and triggers
- Healing goals and progress
- Previous conversations and context

Memory persists across sessions, allowing Rose to provide personalized, continuous support.

## 🛠️ Development

> **📖 Full Development Guide**: See **[DEVELOPMENT.md](DEVELOPMENT.md)** for comprehensive development instructions, troubleshooting, configuration details, and common issues.

### 📁 Project Structure

Following Uncle Bob's Clean Code principles, the project maintains a clear, organized structure:

#### 🗂️ Root Directory
```
Rose/
├── 📂 src/              # Python source code (AI companion logic)
├── 📂 frontend/         # React TypeScript UI
├── 📂 tests/            # Test suite (>70% coverage)
├── 📂 scripts/          # Development and deployment scripts
├── 📂 docs/             # Documentation and archived notes
├── 📂 config/           # Configuration templates
├── 📂 docker/           # Docker-related files
├── 📂 notebooks/        # Jupyter notebooks for exploration
├── 📂 img/              # Project images and assets
├── 📄 pyproject.toml    # Python project config
├── 📄 uv.lock           # Locked Python dependencies
├── 📄 Dockerfile        # Production Docker build
├── 📄 docker-compose.yml # Container orchestration
├── 📄 Makefile          # Common development tasks
└── 📄 README.md         # You are here!
```

> **🧹 Clean Code**: Cache directories (.pytest_cache, .mypy_cache, .ruff_cache), temporary data (long_term_memory/, short_term_memory/), and debug markdown files are gitignored and excluded from Docker builds via .dockerignore

#### 🧠 Source Code Structure
```
src/ai_companion/
├── config/            # 🎯 Configuration constants (ports, paths, timeouts)
├── core/              # Prompts, schedules, utilities
├── graph/             # LangGraph workflow (nodes, edges, state)
├── interfaces/        # Web API and future interfaces
├── modules/           # Memory, speech, image (frozen)
└── settings.py        # Configuration management
```

#### 🎨 Frontend Structure
```
frontend/
├── src/
│   ├── components/    # React components (VoiceButton, etc.)
│   ├── hooks/         # Custom hooks (audio recording, playback)
│   ├── services/      # API client
│   └── config/        # Frontend configuration constants
└── package.json       # Node.js dependencies
```

#### 🚀 Scripts
```
scripts/
├── run_dev_server.py      # 🚀 Start development servers
└── build_and_serve.py     # 📦 Build and serve production
```

### ⚡ Available Commands

```bash
# 🚀 Development (Recommended)
python scripts/run_dev_server.py    # Start both frontend and backend with hot reload
python scripts/build_and_serve.py   # Build frontend and start production server

# 🎨 Code Quality
make format-fix        # Format code with ruff
make lint-fix          # Fix linting issues
make format-check      # Check formatting
make lint-check        # Check linting

# 🐳 Docker (Alternative)
make rose-build        # Build Docker image
make rose-stop         # Stop containers
make rose-delete       # Clean up volumes and containers
```

### 🧪 Testing

Rose has a comprehensive test suite with >70% code coverage:

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src --cov-report=html

# Run specific test categories
uv run pytest tests/unit/                    # Unit tests only
uv run pytest tests/integration/             # Integration tests only
uv run pytest tests/test_performance_benchmarks.py  # Performance tests

# Run type checking
uv run mypy src/

# View coverage report
# Open htmlcov/index.html in your browser
```

**Test Organization**:
- `tests/unit/` - Unit tests for individual modules (memory, speech, error handling)
- `tests/integration/` - End-to-end workflow tests
- `tests/fixtures/` - Shared test fixtures and mock data
- `tests/test_performance_benchmarks.py` - Performance benchmarks for critical operations

**Test Fixtures**:
- Mock Groq, ElevenLabs, and Qdrant clients
- Sample audio files (WAV, MP3)
- Test configuration overrides

See [tests/README.md](tests/README.md) for detailed testing documentation.

## 🚢 Deployment

### 🚂 Railway Deployment

1. **Create a Railway project**
   - Go to [Railway](https://railway.app/)
   - Create a new project from GitHub repo

2. **Configure environment variables**
   Add all required variables from `.env.example` in Railway dashboard

3. **Deploy**
   Railway will automatically detect `config/railway.json` and deploy

### 🌐 Alternative Platforms

Rose can be deployed to any platform supporting Docker or Python applications:
- **Render**: Use `Dockerfile` for deployment
- **Fly.io**: Use `fly.toml` configuration
- **Google Cloud Run**: Use `docker/cloudbuild.yaml`

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment guides.

### 🔄 CI/CD Pipeline

The project includes automated testing and deployment via GitHub Actions:

- **Automated Testing**: Runs on every push and PR
- **Code Coverage**: Tracked via Codecov (70% minimum)
- **Smoke Tests**: Pre-deployment validation
- **Automated Deployment**: Deploys to Railway on main branch

See [CI_CD_SETUP.md](docs/CI_CD_SETUP.md) for setup instructions and configuration details.

## ⚙️ Configuration

### 🤖 Model Selection

Configure models in `.env`:
```bash
TEXT_MODEL_NAME="llama-3.3-70b-versatile"      # Main conversation
SMALL_TEXT_MODEL_NAME="llama-3.1-8b-instant"   # Memory, routing
STT_MODEL_NAME="whisper-large-v3"              # Speech-to-text
```

### 🔊 Voice Configuration

Choose a warm, calming voice for Rose:
```bash
ROSE_VOICE_ID="<elevenlabs-voice-id>"
```

Test different voices at [ElevenLabs Voice Library](https://elevenlabs.io/voice-library)

### 🧠 Memory Settings

Adjust memory behavior in `settings.py`:
- `MEMORY_COLLECTION_NAME`: Qdrant collection name
- `SUMMARIZE_AFTER_N_MESSAGES`: Trigger for conversation summarization
- `MEMORY_TOP_K`: Number of memories to retrieve

## 🗺️ Roadmap

### 🎯 Current Release (v0.1)
- ✅ Voice-first web interface
- ✅ Rose healer shaman personality
- ✅ Groq-powered inference
- ✅ Persistent memory system
- ✅ Railway deployment

### 🔮 Future Releases
- 🔮 WhatsApp integration (code frozen, ready to activate)
- 🔮 Image generation for healing visualizations (code frozen)
- 🔮 Multi-language support
- 🔮 User authentication and profiles
- 🔮 Session history and analytics

## 📂 Project Structure

The project is organized for clarity and maintainability:

- **`src/ai_companion/`** - Python application code
- **`frontend/`** - React voice interface
- **`tests/`** - Comprehensive test suite
- **`docs/`** - Detailed documentation
- **`config/`** - Environment-specific configurations
- **`scripts/`** - Utility scripts (test runners, etc.)
- **`docker/`** - Docker configurations

See [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for detailed structure documentation.

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `make format-fix` and `make lint-fix`
5. Submit a pull request

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph) by LangChain
- Powered by [Groq](https://groq.com/) for fast open-source inference
- Voice synthesis by [ElevenLabs](https://elevenlabs.io/)
- Vector search by [Qdrant](https://qdrant.tech/)

---

**Note**: Rose is an AI companion for emotional support and is not a replacement for professional mental health services. If you're experiencing a mental health crisis, please contact a qualified healthcare provider or crisis helpline.
