# Technology Stack

## Build System & Package Management

- **Package Manager**: `uv` (modern Python package manager)
- **Python Version**: 3.12+
- **Dependency Management**: `pyproject.toml` with `uv.lock`

## Core Frameworks & Libraries

- **LangGraph**: Workflow orchestration and state management
- **LangChain**: LLM integration and tooling
- **Chainlit**: Web-based chat interface
- **FastAPI**: REST API for WhatsApp webhook
- **Pydantic**: Settings management and data validation

## AI/ML Services

- **Groq**: Primary LLM provider (llama-3.3-70b, gemma2-9b, whisper, llama-3.2-vision)
- **ElevenLabs**: Text-to-speech (eleven_flash_v2_5)
- **Together AI**: Image generation (FLUX.1-schnell)
- **Sentence Transformers**: Embeddings for vector search

## Data & Memory

- **Qdrant**: Vector database for long-term memory
- **DuckDB/SQLite**: Short-term conversation checkpointing
- **LangGraph Checkpointers**: Conversation state persistence

## Code Quality

- **Ruff**: Linting and formatting
- **Pre-commit**: Git hooks for code quality
- Line length: 120 characters
- Import sorting enabled

## Common Commands

### Development
```bash
# Install dependencies
uv sync

# Format code
make format-fix

# Lint code
make lint-fix

# Check formatting and linting
make format-check
make lint-check
```

### Docker Deployment
```bash
# Build and run all services
make ava-build
make ava-run

# Stop services
make ava-stop

# Clean up (removes memory databases and containers)
make ava-delete
```

### Running Services Locally
```bash
# Run with uv
uv run <command>

# Chainlit interface (port 8000)
chainlit run <app_file>

# WhatsApp webhook (port 8080)
fastapi run src/ai_companion/interfaces/whatsapp/webhook_endpoint.py
```

## Environment Configuration

Required environment variables (see `.env.example`):
- `GROQ_API_KEY`
- `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`
- `TOGETHER_API_KEY`
- `QDRANT_URL`, `QDRANT_API_KEY`
- `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_TOKEN`, `WHATSAPP_VERIFY_TOKEN`

Settings are managed via `pydantic-settings` in `src/ai_companion/settings.py`.
