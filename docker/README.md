# Docker Configuration

This directory contains Docker-related configuration files for building and deploying Rose.

> **Note:** Rose now includes a modern voice-first web interface served through FastAPI. For local development, we recommend using `python scripts/run_dev_server.py` instead of Docker Compose. See [DEVELOPMENT.md](../DEVELOPMENT.md) for details.

## Files

### Dockerfile.chainlit
Docker configuration for the Chainlit web interface.

**Purpose:** Builds a containerized version of Rose's Chainlit chat interface for local development and testing.

**Usage:**
```bash
# Build the image
docker build -f docker/Dockerfile.chainlit -t rose-chainlit .

# Run the container
docker run -p 8000:8000 --env-file .env rose-chainlit
```

**Or use docker-compose:**
```bash
docker-compose up chainlit
```

### cloudbuild.yaml
Google Cloud Build configuration for deploying to Google Cloud Run.

**Purpose:** Defines the build and deployment process for Google Cloud Platform.

**Usage:**
```bash
# Deploy to Cloud Run
gcloud builds submit --config=docker/cloudbuild.yaml
```

**Configuration:**
- Builds Docker image from root Dockerfile
- Pushes to Google Container Registry
- Deploys to Cloud Run with specified settings

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

## Docker Compose

The `docker-compose.yml` file remains in the project root for easy access.

**Location:** `/docker-compose.yml` (root directory)

**Services:**
- `chainlit` - Web chat interface (port 8000)
- `qdrant` - Vector database for long-term memory (port 6333)

**Usage:**
```bash
# Start all services
docker-compose up

# Start specific service
docker-compose up chainlit

# Build and start
docker-compose up --build

# Stop all services
docker-compose down
```

## Building Images

### Development Build
```bash
# Build Chainlit interface
docker-compose build chainlit

# Or build directly
docker build -f docker/Dockerfile.chainlit -t rose-chainlit .
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
- `TOGETHER_API_KEY` - Together AI for image generation
- `QDRANT_URL` - Qdrant vector database URL
- `QDRANT_API_KEY` - Qdrant API key (if using cloud)

**Optional:**
- `PORT` - Server port (default: 8080)
- `HOST` - Server host (default: 0.0.0.0)
- `LOG_LEVEL` - Logging level (default: INFO)

See `.env.example` for complete list.

## Volumes

### Persistent Data
Docker Compose configures volumes for data persistence:

- `long_term_memory/` - Qdrant vector database storage
- `short_term_memory/` - SQLite conversation checkpoints
- `generated_images/` - Generated image outputs

These directories are automatically created and mounted.

## Networking

### Internal Network
Docker Compose creates a bridge network for service communication:

- Chainlit → Qdrant: `http://qdrant:6333`
- API → Qdrant: `http://qdrant:6333`

### External Access
- Chainlit UI: http://localhost:8000
- Qdrant API: http://localhost:6333
- API Server: http://localhost:8080

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
