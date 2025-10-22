# Deployment Configuration Guide

This document provides detailed information about deployment configuration for Rose the Healer Shaman, including environment-specific settings, resource limits, and optimization strategies.

## Table of Contents

1. [Overview](#overview)
2. [Environment-Specific Configuration](#environment-specific-configuration)
3. [Railway Configuration](#railway-configuration)
4. [Docker Configuration](#docker-configuration)
5. [Resource Limits](#resource-limits)
6. [Health Check Configuration](#health-check-configuration)
7. [Volume Setup](#volume-setup)
8. [Optimization Strategies](#optimization-strategies)

## Overview

Rose supports three deployment environments:
- **Development**: Local development with relaxed security and verbose logging
- **Staging**: Pre-production testing with production-like settings
- **Production**: Live deployment with strict security and optimized performance

Each environment has specific configuration files in the `config/` directory.

## Environment-Specific Configuration

### Development Environment

**File**: `config/dev.env`

**Purpose**: Local development and testing

**Key Settings**:
```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
LOG_FORMAT=console
ALLOWED_ORIGINS="*"
RATE_LIMIT_ENABLED=false
ENABLE_API_DOCS=true
WORKFLOW_TIMEOUT_SECONDS=120
SESSION_RETENTION_DAYS=1
```

**Characteristics**:
- Verbose logging for debugging
- No rate limiting
- Relaxed CORS policy
- Longer timeouts for debugging
- Daily session cleanup for testing
- API documentation enabled

**Use Cases**:
- Local development
- Feature testing
- Debugging issues
- Integration testing

### Staging Environment

**File**: `config/staging.env`

**Purpose**: Pre-production testing and validation

**Key Settings**:
```bash
ENVIRONMENT=staging
LOG_LEVEL=INFO
LOG_FORMAT=json
ALLOWED_ORIGINS="https://staging.yourdomain.com"
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=20
ENABLE_API_DOCS=true
WORKFLOW_TIMEOUT_SECONDS=60
SESSION_RETENTION_DAYS=3
```

**Characteristics**:
- Structured JSON logging
- Moderate rate limiting
- Restricted CORS to staging domain
- Production-like timeouts
- Shorter session retention
- API docs enabled for testing

**Use Cases**:
- Pre-production testing
- QA validation
- Performance testing
- Integration testing with real services
- Client demos

### Production Environment

**File**: `config/prod.env`

**Purpose**: Live production deployment

**Key Settings**:
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
LOG_FORMAT=json
ALLOWED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=10
ENABLE_API_DOCS=false
WORKFLOW_TIMEOUT_SECONDS=60
SESSION_RETENTION_DAYS=7
```

**Characteristics**:
- Structured JSON logging
- Strict rate limiting
- Restricted CORS to production domains
- Strict timeouts
- Standard session retention
- API docs disabled for security

**Use Cases**:
- Live production traffic
- Real user interactions
- Production monitoring
- Business operations

## Railway Configuration

### Configuration Files

Railway uses JSON configuration files to define build and deployment settings:

| File | Environment | Workers | Use Case |
|------|-------------|---------|----------|
| `config/railway.json` | Default | 2 | General purpose |
| `config/railway-staging.json` | Staging | 2 | Pre-production |
| `config/railway-prod.json` | Production | 4 | Live production |

### Railway Configuration Structure

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "uv sync --frozen && cd frontend && npm install && npm run build"
  },
  "deploy": {
    "startCommand": "uvicorn ai_companion.interfaces.web.app:app --host 0.0.0.0 --port $PORT --workers 4",
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 30,
    "healthcheckInterval": 10,
    "startPeriod": 40,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3,
    "numReplicas": 1,
    "sleepApplication": false
  }
}
```

### Configuration Parameters

#### Build Configuration

- **builder**: `NIXPACKS` - Railway's automatic builder
- **buildCommand**: Multi-step build process:
  1. `uv sync --frozen` - Install Python dependencies
  2. `cd frontend && npm install` - Install frontend dependencies
  3. `npm run build` - Build frontend assets

#### Deploy Configuration

- **startCommand**: Uvicorn server with configurable workers
- **healthcheckPath**: Endpoint for health verification
- **healthcheckTimeout**: Maximum time for health check response (30s)
- **healthcheckInterval**: Time between health checks (10s)
- **startPeriod**: Grace period before first health check (40s)
- **restartPolicyType**: Restart on failure
- **restartPolicyMaxRetries**: Maximum restart attempts (3)
- **numReplicas**: Number of instances (1 for now)
- **sleepApplication**: Keep service always running (false)

### Worker Configuration

Workers are Uvicorn worker processes that handle concurrent requests:

| Environment | Workers | RAM Required | Capacity |
|-------------|---------|--------------|----------|
| Development | 1 | 256MB | 5-10 users |
| Staging | 2 | 512MB-2GB | 10-20 users |
| Production | 4 | 4-8GB | 50-100 users |

**Worker Calculation**:
- Formula: `workers = (2 × CPU cores) + 1`
- Each worker uses ~100-200MB RAM
- More workers = better concurrency but higher memory usage

## Docker Configuration

### Multi-Stage Build

The Dockerfile uses a 3-stage build process:

1. **Frontend Builder**: Builds React frontend
2. **Python Builder**: Installs Python dependencies
3. **Runtime**: Minimal runtime image without build tools

### Stage 1: Frontend Builder

```dockerfile
FROM node:20-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
```

**Purpose**: Build optimized frontend assets
**Output**: `/frontend/dist` directory with production build

### Stage 2: Python Builder

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS python-builder
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential g++
COPY uv.lock pyproject.toml README.md /app/
RUN uv sync --frozen --no-cache
COPY src/ /app/src/
RUN uv pip install -e .
```

**Purpose**: Install Python dependencies with build tools
**Output**: `/app/.venv` virtual environment

### Stage 3: Runtime

```dockerfile
FROM python:3.12-slim-bookworm
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1
COPY --from=python-builder /app/.venv /app/.venv
COPY --from=python-builder /app/src /app/src
COPY --from=frontend-builder /frontend/dist /app/frontend/build
RUN mkdir -p /app/data /app/data/backups
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
VOLUME ["/app/data"]
```

**Purpose**: Minimal runtime image without build dependencies
**Size Optimization**:
- No build tools (gcc, g++, make)
- Only runtime dependencies (libgomp1)
- Non-root user for security
- Clean apt cache

### Docker Compose Configuration

```yaml
services:
  whatsapp:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    env_file:
      - .env
    volumes: 
      - ./short_term_memory:/app/data
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

**Resource Limits**:
- **Memory Limit**: 512MB maximum
- **Memory Reservation**: 256MB guaranteed
- **Purpose**: Prevent OOM kills and resource exhaustion

## Resource Limits

### Memory Limits

Memory limits prevent resource exhaustion and ensure predictable performance:

#### Railway Plans

| Plan | RAM | Recommended Workers | Expected Capacity |
|------|-----|---------------------|-------------------|
| Starter | 512MB | 1-2 | 10-20 users |
| Developer | 8GB | 2-4 | 50-100 users |
| Pro | 32GB | 4-8 | 200-500 users |

#### Memory Usage Breakdown

Per worker memory usage:
- **Base Python Runtime**: ~50MB
- **Dependencies (LangChain, FastAPI)**: ~100MB
- **Per Request**: ~10-20MB
- **Total per Worker**: ~150-200MB

Example for 4 workers:
- Workers: 4 × 200MB = 800MB
- Overhead: ~200MB
- **Total**: ~1GB minimum

### CPU Limits

Railway provides shared or dedicated CPU based on plan:
- **Starter**: Shared CPU (throttled)
- **Developer**: Dedicated CPU (1-2 cores)
- **Pro**: Dedicated CPU (4+ cores)

### Disk Limits

Volume storage for persistent data:
- **Minimum**: 1GB (development/staging)
- **Recommended**: 5GB (production)
- **Growth Rate**: ~1MB per 100 conversations

### Network Limits

Railway provides generous bandwidth:
- **Included**: 100GB/month (Starter)
- **Overage**: $0.10/GB
- **Typical Usage**: ~10-50GB/month for moderate traffic

## Health Check Configuration

### Health Check Endpoint

**Path**: `/api/health`

**Response**:
```json
{
  "status": "healthy",
  "services": {
    "groq": "connected",
    "elevenlabs": "connected",
    "qdrant": "connected",
    "database": "connected"
  },
  "timestamp": "2024-10-21T12:00:00Z"
}
```

### Health Check Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| healthcheckPath | `/api/health` | Endpoint to check |
| healthcheckTimeout | 30s | Max response time |
| healthcheckInterval | 10s | Time between checks |
| startPeriod | 40s | Grace period on startup |

### Start Period (Grace Period)

The `startPeriod` gives your application time to initialize before health checks begin.

**Why 40 seconds?**
- Python runtime initialization: ~5s
- Dependency loading: ~10s
- Database connections: ~5s
- External service verification: ~10s
- Buffer: ~10s

**When to increase**:
- Large model loading
- Slow external services
- Cold start issues
- Complex initialization

**How to adjust**:
```json
{
  "deploy": {
    "startPeriod": 60  // Increase to 60s if needed
  }
}
```

### Health Check Failure Handling

Railway's restart policy:
1. Health check fails
2. Wait for next interval (10s)
3. Retry health check
4. If still failing, restart service
5. Maximum 3 restart attempts
6. If all retries fail, mark service as unhealthy

## Volume Setup

### Why Volumes Are Critical

Without persistent volumes, you lose:
- Conversation history (SQLite database)
- User session data
- Backup files
- Temporary audio files

### Volume Configuration

**Mount Path**: `/app/data`

**Contents**:
```
/app/data/
├── short_term_memory.db    # SQLite checkpoints
├── backups/                # Automated backups
│   ├── memory_20241021_030000.db
│   └── memory_20241022_030000.db
└── temp/                   # Temporary audio files
```

### Setting Up Volumes in Railway

1. Navigate to service in Railway dashboard
2. Go to "Settings" tab
3. Scroll to "Volumes" section
4. Click "Add Volume"
5. Configure:
   - **Mount Path**: `/app/data`
   - **Size**: 1GB (staging) or 5GB (production)
6. Click "Add"

### Volume Best Practices

1. **Size Planning**:
   - 1GB: ~10,000 conversations
   - 5GB: ~50,000 conversations
   - 10GB: ~100,000 conversations

2. **Monitoring**:
   - Check usage weekly
   - Set up alerts at 80% capacity
   - Plan for growth

3. **Backup Strategy**:
   - Automated daily backups
   - 7-day retention
   - Stored in `/app/data/backups/`

4. **Cleanup**:
   - Automatic session cleanup (configurable)
   - Temporary file cleanup (hourly)
   - Old backup cleanup (weekly)

## Optimization Strategies

### Memory Optimization

1. **Reduce Workers**: Lower worker count if memory is constrained
2. **Session Cleanup**: Decrease retention days to reduce database size
3. **Lazy Loading**: Load heavy dependencies only when needed
4. **Connection Pooling**: Reuse database connections

### Performance Optimization

1. **Worker Tuning**: Adjust workers based on CPU cores
2. **Caching**: Implement response caching for common queries
3. **Database Indexing**: Add indexes for frequent queries
4. **CDN**: Use CDN for static frontend assets

### Cost Optimization

1. **Right-Size Plan**: Choose appropriate Railway plan
2. **Sleep Unused Services**: Enable sleep for staging
3. **Optimize Images**: Minimize Docker image size
4. **Efficient Logging**: Use appropriate log levels

### Startup Optimization

1. **Lazy Imports**: Import heavy libraries only when needed
2. **Async Initialization**: Initialize services in parallel
3. **Connection Pooling**: Reuse connections across requests
4. **Preload Models**: Load ML models during startup, not per request

## Configuration Checklist

### Before Deployment

- [ ] Choose appropriate environment (staging/production)
- [ ] Copy correct railway.json configuration
- [ ] Set all required environment variables
- [ ] Configure CORS origins for your domain
- [ ] Set up persistent volume
- [ ] Configure resource limits
- [ ] Enable security headers
- [ ] Set appropriate log level
- [ ] Configure rate limiting
- [ ] Disable API docs in production

### After Deployment

- [ ] Verify health check passes
- [ ] Test API endpoints
- [ ] Verify volume persistence
- [ ] Check logs for errors
- [ ] Monitor memory usage
- [ ] Test voice interaction
- [ ] Verify session persistence
- [ ] Set up monitoring alerts

## Troubleshooting

### High Memory Usage

**Symptoms**: Service crashes with OOM error

**Solutions**:
1. Reduce number of workers
2. Decrease session retention days
3. Verify cleanup jobs are running
4. Upgrade Railway plan

### Slow Startup

**Symptoms**: Health checks timeout during startup

**Solutions**:
1. Increase `startPeriod` to 60-90s
2. Optimize dependency loading
3. Use lazy imports
4. Check external service latency

### Volume Not Persisting

**Symptoms**: Data lost after restart

**Solutions**:
1. Verify volume mount path is `/app/data`
2. Check volume status in Railway dashboard
3. Ensure database path points to volume
4. Review deployment logs

### Health Check Failures

**Symptoms**: Service marked unhealthy

**Solutions**:
1. Check external service connectivity
2. Verify API keys are valid
3. Increase health check timeout
4. Review application logs

## Additional Resources

- [Railway Setup Guide](RAILWAY_SETUP.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Operations Runbook](OPERATIONS_RUNBOOK.md)
- [Rollback Procedures](ROLLBACK_PROCEDURES.md)

## Summary

Proper deployment configuration is critical for production readiness:

1. **Use environment-specific configs** for development, staging, and production
2. **Configure health checks** with appropriate grace periods
3. **Set up persistent volumes** to prevent data loss
4. **Optimize resource limits** based on your Railway plan
5. **Monitor and adjust** based on actual usage patterns

Following these guidelines ensures a stable, performant, and cost-effective deployment.
