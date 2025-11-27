# Docker Configuration

This directory contains Docker-related configuration files for building and deploying Rose.

> **Note:** Rose now includes a modern voice-first web interface served through FastAPI. For local development, we recommend using `python scripts/run_dev_server.py` instead of Docker Compose. See [DEVELOPMENT.md](../DEVELOPMENT.md) for details.

## Files

### Dockerfile.backend.dev
Development Dockerfile for the backend with hot-reload support.

**Usage:**
```bash
docker-compose -f docker-compose.dev.yml up backend
```

### Dockerfile.frontend.dev
Development Dockerfile for the React frontend with Vite dev server.

**Usage:**
```bash
docker-compose -f docker-compose.dev.yml up frontend
```

### cloudbuild.yaml
Google Cloud Build configuration for deploying to Google Cloud Run.

**Purpose:** Defines the build and deployment process for Google Cloud Platform.

**Usage:**
```bash
# Deploy to Cloud Run
gcloud builds submit --config=docker/cloudbuild.yaml
```

## Main Dockerfile

The main `Dockerfile` remains in the project root for Railway and other platforms that expect it there.

**Location:** `/Dockerfile` (root directory)

**Purpose:** Production-ready multi-stage Docker build for the Rose API server.

**Features:**
- Multi-stage build for optimized image size
- Python 3.12 with uv package manager
- Frontend build integration
- Health check configuration
- Non-root user for security

## Docker Compose Files

### docker-compose.yml (Production)
**Location:** `/docker-compose.yml` (root directory)

**Services:**
- `rose` - FastAPI web interface (port 8000)
- `qdrant` - Vector database for long-term memory (port 6335)

**Usage:**
```bash
docker-compose up --build
```

### docker-compose.dev.yml (Development)
**Location:** `/docker-compose.dev.yml` (root directory)

**Services:**
- `backend` - FastAPI with hot-reload (port 8000)
- `frontend` - Vite dev server (port 3000)
- `qdrant` - Vector database (port 6333)

**Usage:**
```bash
docker-compose -f docker-compose.dev.yml up
```

## Building Images

### Development Build
```bash
# Start dev environment with docker-compose
docker-compose -f docker-compose.dev.yml up --build
```

### Production Build
```bash
# Build main application
docker build -t rose-api .

# Test the build
docker run -p 8080:8080 --env-file .env rose-api
```

## Environment Variables

All Docker containers require environment variables from `.env` file:

**Required:**
- `GROQ_API_KEY` - Groq API for LLM and STT
- `ELEVENLABS_API_KEY` - ElevenLabs for TTS
- `ELEVENLABS_VOICE_ID` - Voice ID for Rose
- `QDRANT_URL` - Qdrant vector database URL
- `QDRANT_API_KEY` - Qdrant API key (if using cloud)

**Optional:**
- `PORT` - Server port (default: 8080 production, 8000 development)
- `HOST` - Server host (default: 0.0.0.0)
- `LOG_LEVEL` - Logging level (default: INFO)

See `.env.example` for complete list.

## Volumes

### Persistent Data
Docker Compose configures volumes for data persistence:

- `long_term_memory/` - Qdrant vector database storage
- `short_term_memory/` - SQLite conversation checkpoints

These directories are automatically created and mounted.

## Port Configuration

| Environment | Service | Internal Port | External Port |
|-------------|---------|---------------|---------------|
| Production  | rose    | 8000          | 8000          |
| Production  | qdrant  | 6333          | 6335          |
| Development | backend | 8000          | 8000          |
| Development | frontend| 3000          | 3000          |
| Development | qdrant  | 6333          | 6333          |
| Railway     | rose    | 8080          | 8080          |

## Networking

### Internal Network
Docker Compose creates a bridge network for service communication:

- Backend → Qdrant: `http://qdrant:6333`

### External Access
- Production UI: http://localhost:8000
- Dev Frontend: http://localhost:3000
- Dev Backend: http://localhost:8000
- Qdrant API: http://localhost:6333 (dev) or http://localhost:6335 (prod)

## Troubleshooting

### Container Won't Start
1. Check environment variables are set
2. Verify ports are not already in use
3. Check Docker logs: `docker-compose logs [service]`

### Build Failures
1. Clear Docker cache: `docker-compose build --no-cache`
2. Check Dockerfile syntax
3. Verify base image availability

### Volume Permission Issues
1. Check directory permissions
2. Run with appropriate user: `docker-compose up --user $(id -u):$(id -g)`

### Network Issues
1. Verify service names in URLs
2. Check Docker network: `docker network inspect rose_default`
3. Restart Docker daemon if needed

## Best Practices

1. **Use .dockerignore** - Exclude unnecessary files from build context
2. **Multi-stage builds** - Keep production images small
3. **Non-root user** - Run containers as non-root for security
4. **Health checks** - Define health check endpoints
5. **Environment variables** - Never hardcode secrets
6. **Volume mounts** - Persist important data
7. **Resource limits** - Set memory and CPU limits in production

## Related Documentation

- [Deployment Guide](../docs/DEPLOYMENT.md)
- [Railway Setup](../docs/RAILWAY_SETUP.md)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
