# Project Structure

This document describes the organization of the Rose the Healer Shaman project.

## Root Directory

The root directory contains only essential configuration files:

```
rose/
├── .env.example              # Environment variable template
├── .gitignore                # Git ignore patterns
├── .pre-commit-config.yaml   # Pre-commit hooks configuration
├── .python-version           # Python version specification
├── docker-compose.yml        # Docker Compose orchestration
├── Dockerfile                # Main production Docker image
├── LICENSE                   # MIT License
├── Makefile                  # Build automation commands
├── pyproject.toml            # Python project configuration
├── README.md                 # Project documentation
└── uv.lock                   # Dependency lock file
```

## Directory Structure

### `.github/`
GitHub-specific configuration and workflows.

```
.github/
├── codecov.yml               # Code coverage configuration
└── workflows/
    ├── test.yml              # CI/CD test workflow
    └── status-check.yml      # Status check workflow
```

### `.kiro/`
Kiro AI assistant configuration and specifications.

```
.kiro/
├── specs/                    # Feature specifications
│   ├── deployment-readiness-review/
│   ├── playai-tts-migration/
│   └── rose-transformation/
└── steering/                 # AI assistant steering rules
```

### `config/`
Environment-specific configuration files.

```
config/
├── dev.env                   # Development environment template
├── staging.env               # Staging environment template
├── prod.env                  # Production environment template
├── railway-staging.json      # Railway staging configuration
├── railway-prod.json         # Railway production configuration
├── railway.json              # Default Railway configuration
├── langgraph.json            # LangGraph Studio configuration
└── README.md                 # Configuration documentation
```

### `docker/`
Docker-related configuration files.

```
docker/
├── Dockerfile.chainlit       # Chainlit interface Docker image
├── cloudbuild.yaml           # Google Cloud Build configuration
└── README.md                 # Docker documentation
```

### `docs/`
Project documentation.

```
docs/
├── API_DOCUMENTATION.md
├── ARCHITECTURE.md
├── CIRCUIT_BREAKERS.md
├── CI_CD_SETUP.md
├── CODE_QUALITY_IMPROVEMENTS.md
├── DATA_PERSISTENCE.md
├── DEPLOYMENT.md
├── DEPLOYMENT_CONFIGURATION.md
├── EXTERNAL_API_LIMITS.md
├── GETTING_STARTED.md
├── INCIDENT_RESPONSE_PLAN.md
├── MONITORING_AND_OBSERVABILITY.md
├── OPERATIONS_RUNBOOK.md
├── PROJECT_STRUCTURE.md         # This file
├── RAILWAY_SETUP.md
├── RESOURCE_MANAGEMENT.md
├── ROLLBACK_PROCEDURES.md
├── SECURITY.md
├── TESTING_COMPLETE.md
└── [implementation summaries]
```

### `frontend/`
React-based voice interface.

```
frontend/
├── src/                      # React source code
│   ├── components/           # React components
│   ├── hooks/                # Custom React hooks
│   └── App.tsx               # Main application
├── public/                   # Static assets
├── index.html                # HTML entry point
├── package.json              # Node.js dependencies
├── vite.config.ts            # Vite configuration
└── README.md                 # Frontend documentation
```

### `img/`
Project images and assets.

```
img/
├── ava_final_design.gif
├── beam_logo.png
├── project_overview_diagram.gif
└── [other images]
```

### `notebooks/`
Jupyter notebooks for experimentation.

```
notebooks/
├── character_card.ipynb      # Character development
└── router.ipynb              # Routing logic experiments
```

### `scripts/`
Utility scripts for development and testing.

```
scripts/
├── run_tests.sh              # Unix/Linux/Mac test runner
├── run_tests.bat             # Windows test runner
├── fix-secret.sh             # Git history cleanup
└── README.md                 # Scripts documentation
```

### `src/`
Python source code for the AI companion.

```
src/ai_companion/
├── core/                     # Core utilities
│   ├── exceptions.py         # Custom exceptions
│   ├── error_handlers.py     # Error handling decorators
│   ├── resilience.py         # Circuit breakers
│   ├── backup.py             # Database backup
│   ├── prompts.py            # System prompts
│   └── schedules.py          # Activity scheduling
├── graph/                    # LangGraph workflow
│   ├── graph.py              # Workflow construction
│   ├── state.py              # State schema
│   ├── nodes.py              # Workflow nodes
│   ├── edges.py              # Conditional edges
│   └── utils/                # Graph utilities
├── interfaces/               # User interfaces
│   ├── chainlit/             # Chainlit web interface
│   └── web/                  # FastAPI web interface
│       ├── app.py            # FastAPI application
│       ├── middleware.py     # Security middleware
│       └── routes/           # API routes
├── modules/                  # Feature modules
│   ├── image/                # Image generation
│   ├── memory/               # Memory management
│   │   ├── long_term/        # Qdrant vector memory
│   │   └── short_term/       # SQLite checkpointer
│   ├── schedules/            # Schedule management
│   └── speech/               # Speech processing
│       ├── speech_to_text.py # STT with Groq
│       └── text_to_speech.py # TTS with ElevenLabs
└── settings.py               # Application settings
```

### `tests/`
Test suite for the application.

```
tests/
├── test_core.py              # Core functionality tests
├── test_circuit_breaker.py   # Circuit breaker tests
├── test_voice_interaction.py # Voice flow tests
├── test_rose_character.py    # Character tests
├── test_memory_therapeutic.py # Memory tests
├── test_frontend_automated.py # Frontend automation
├── test_frontend_manual.md   # Manual test checklist
├── test_performance.py       # Performance tests
├── test_deployment.py        # Deployment tests
├── test_security.py          # Security tests
├── test_data_persistence.py  # Data persistence tests
├── test_smoke.py             # Smoke tests
├── locustfile.py             # Load testing
├── pytest.ini                # Pytest configuration
├── README.md                 # Testing documentation
└── TESTING_SUMMARY.md        # Test implementation summary
```

## File Organization Principles

### Root Directory
**Only essential files that must be in root:**
- Configuration files required by tools (pyproject.toml, Dockerfile, etc.)
- Primary documentation (README.md, LICENSE)
- Environment templates (.env.example)
- Version control configuration (.gitignore, .python-version)

### Subdirectories
**All other files organized by purpose:**
- **config/** - All configuration variants
- **docker/** - All Docker-related files except main Dockerfile
- **docs/** - All documentation except README
- **scripts/** - All utility scripts
- **tests/** - All test files and test configuration

## Benefits of This Structure

1. **Clean Root** - Easy to find essential files
2. **Logical Grouping** - Related files together
3. **Scalability** - Easy to add new files without cluttering root
4. **Discoverability** - Clear where to find specific types of files
5. **Maintainability** - Easier to manage and update

## Finding Files

### Configuration Files
- **Environment config**: `config/` directory
- **Railway config**: `config/railway*.json`
- **Docker config**: `docker/` directory
- **Test config**: `tests/pytest.ini`
- **CI/CD config**: `.github/workflows/`

### Documentation
- **Getting started**: `README.md` (root)
- **Detailed docs**: `docs/` directory
- **API docs**: `docs/API_DOCUMENTATION.md`
- **Deployment**: `docs/DEPLOYMENT.md`

### Scripts
- **Test runners**: `scripts/run_tests.*`
- **Utility scripts**: `scripts/` directory

### Source Code
- **Application code**: `src/ai_companion/`
- **Tests**: `tests/`
- **Frontend**: `frontend/`

## Migration Notes

Files were reorganized from root to subdirectories:

**Moved to `scripts/`:**
- `run_tests.sh`
- `run_tests.bat`
- `fix-secret.sh`

**Moved to `docker/`:**
- `Dockerfile.chainlit`
- `cloudbuild.yaml`

**Moved to `config/`:**
- `railway.json`
- `langgraph.json`

**Moved to `tests/`:**
- `pytest.ini`

**Moved to `docs/`:**
- `TESTING_COMPLETE.md`

**Moved to `.github/`:**
- `codecov.yml`

All references in code and documentation have been updated accordingly.

## Related Documentation

- [Getting Started](GETTING_STARTED.md)
- [Architecture](ARCHITECTURE.md)
- [Deployment](DEPLOYMENT.md)
- [Testing](../tests/README.md)
- [Configuration](../config/README.md)
- [Scripts](../scripts/README.md)
- [Docker](../docker/README.md)
