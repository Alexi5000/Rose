# Docker Configuration Analysis & Fixes

**Generated:** 2025-11-24
**Status:** Critical issues found that may cause connection and performance problems

---

## 🔴 Critical Issues Found

### 1. Port Configuration Mismatch

**Issue:** Multiple port mismatches between Dockerfile and docker-compose.yml

**Current State:**
- Dockerfile EXPOSE: `8080`
- docker-compose PORT env: `8000`
- docker-compose port mapping: `"8000:8000"`
- Qdrant port mapping: `"6335:6333"` (exposing on host port 6335 instead of 6333)

**Impact:**
- Application may fail to start or be unreachable
- Qdrant might not be accessible from host at expected port

**Fix:** Standardize on port 8000 throughout

### 2. Memory Limits Too Low

**Issue:** Rose container limited to 512M RAM

**Current State:**
```yaml
deploy:
  resources:
    limits:
      memory: 512M
    reservations:
      memory: 256M
```

**Impact:**
- Sentence transformer model (all-MiniLM-L6-v2) requires ~200MB
- LLM inference can spike to 300-500MB
- Total runtime can easily exceed 512M causing OOM kills
- Container restarts = conversation loss

**Recommended:**
```yaml
deploy:
  resources:
    limits:
      memory: 1G
    reservations:
      memory: 512M
```

### 3. Missing Health Check for Rose Container

**Issue:** Qdrant has a health check, but Rose doesn't have a proper one configured

**Current State:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8080}/api/health')" || exit 1
```

This uses PORT variable which is 8000, but defaults to 8080 if not set.

**Fix:** Use the correct port explicitly or ensure consistency

### 4. No Resource Limits for Qdrant

**Issue:** Qdrant has no memory limits, can consume unlimited RAM

**Recommended:**
```yaml
qdrant:
  deploy:
    resources:
      limits:
        memory: 1G
      reservations:
        memory: 512M
```

---

## ✅ Recommended Configuration

### docker-compose.yml (Fixed)

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"  # FIXED: Was 6335:6333
    volumes:
      - ./long_term_memory:/qdrant/storage
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "bash -c '</dev/tcp/localhost/6333'"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    deploy:
      resources:
        limits:
          memory: 1G  # NEW: Added resource limits
        reservations:
          memory: 512M

  rose:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - DOCKER_ENV=true
      - PORT=8000
      - QDRANT_PORT=6333
      - QDRANT_HOST=qdrant
      - QDRANT_URL=http://qdrant:6333
    restart: unless-stopped
    volumes:
      - ./short_term_memory:/app/data
    depends_on:
      qdrant:
        condition: service_healthy
    healthcheck:  # NEW: Added proper health check
      test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')\" || exit 1"]
      interval: 30s
      timeout: 10s
      start_period: 60s  # Increased for model loading
      retries: 3
    deploy:
      resources:
        limits:
          memory: 1G  # INCREASED: Was 512M
        reservations:
          memory: 512M  # INCREASED: Was 256M
```

### Dockerfile (Fixed)

```dockerfile
# ... (no changes needed in build stages) ...

# Stage 3: Runtime image (minimal, no build tools)
FROM python:3.12-slim-bookworm

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Install only runtime dependencies (no build tools)
# libgomp1 is required for some ML libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoremove -y

# Copy frontend build from frontend-builder stage to correct location
# Vite outputs to /frontend/dist, we copy to the path expected by FastAPI
COPY --from=frontend-builder /frontend/dist /app/src/ai_companion/interfaces/web/static

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Create data directories for memory databases and backups
RUN mkdir -p /app/data /app/data/backups && \
    chown -R appuser:appuser /app/data

# Copy virtual environment from builder
COPY --from=python-builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code
COPY --from=python-builder --chown=appuser:appuser /app/src /app/src
COPY --from=python-builder --chown=appuser:appuser /app/pyproject.toml /app/README.md /app/

# Switch to non-root user
USER appuser

# Define volumes
VOLUME ["/app/data"]

# FIXED: Changed from 8080 to 8000 to match docker-compose
EXPOSE 8000

# Health check - FIXED: Use 8000 explicitly
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Run the Rose web interface using uvicorn - FIXED: Use 8000 explicitly
CMD uvicorn ai_companion.interfaces.web.app:app --host 0.0.0.0 --port 8000
```

---

## 🚀 Deployment Steps

### 1. Apply Configuration Fixes

```bash
# Stop current containers
docker-compose down

# Backup current data
cp -r long_term_memory long_term_memory_backup_$(date +%Y%m%d_%H%M%S)
cp -r short_term_memory short_term_memory_backup_$(date +%Y%m%d_%H%M%S)

# Apply the fixed configurations above
# (Update docker-compose.yml and Dockerfile with the recommended configs)
```

### 2. Rebuild and Start

```bash
# Rebuild with no cache to ensure clean build
docker-compose build --no-cache

# Start services
docker-compose up -d

# Watch logs
docker-compose logs -f
```

### 3. Verify Health

```bash
# Check container status
docker-compose ps

# Check health
curl http://localhost:8000/api/v1/health

# Check Qdrant
curl http://localhost:6333/collections

# Check memory system
curl http://localhost:8000/api/v1/admin/memory/status
```

### 4. Monitor Performance

```bash
# Watch container stats
docker stats

# Check for OOM kills
docker-compose logs rose | grep -i "killed\|oom"

# Check Qdrant logs
docker-compose logs qdrant | grep -i "error\|panic"
```

---

## 🔍 Troubleshooting

### Container Keeps Restarting

```bash
# Check logs
docker-compose logs rose --tail=100

# Common issues:
# 1. OOM kill → Increase memory limit
# 2. Port conflict → Check if 8000 or 6333 already in use
# 3. Missing .env → Verify .env file exists with required variables
```

### Memory Issues

```bash
# Check memory usage
docker stats rose qdrant

# If Rose uses >90% of limit:
# - Increase memory limit to 1.5G or 2G
# - Check for memory leaks in logs
# - Consider using smaller model (not recommended)
```

### Qdrant Connection Issues

```bash
# Test Qdrant from inside Rose container
docker-compose exec rose curl http://qdrant:6333/collections

# Test from host
curl http://localhost:6333/collections

# If fails, check:
# - Qdrant container is healthy: docker-compose ps
# - Port mapping is correct: docker-compose port qdrant 6333
# - Network connectivity: docker network inspect rose_default
```

---

## 📊 Performance Tuning

### For Production Deployments

```yaml
rose:
  deploy:
    resources:
      limits:
        memory: 2G  # For production with multiple concurrent users
        cpus: '2'   # Limit CPU usage
      reservations:
        memory: 1G
        cpus: '1'

qdrant:
  deploy:
    resources:
      limits:
        memory: 2G  # For large memory collections
        cpus: '2'
      reservations:
        memory: 1G
        cpus: '1'
```

### Environment Variables for Tuning

Add to `.env`:

```bash
# Memory System
QDRANT_MAX_RETRIES=3
QDRANT_INITIAL_BACKOFF=1.0
QDRANT_MAX_BACKOFF=10.0

# Performance
WORKFLOW_TIMEOUT_SECONDS=120
LLM_TIMEOUT_SECONDS=45
LLM_MAX_RETRIES=3

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

## ✅ Validation Checklist

After applying fixes, verify:

- [ ] Containers start without errors: `docker-compose up -d`
- [ ] Health checks pass: `docker-compose ps` shows "healthy"
- [ ] Rose accessible: `curl http://localhost:8000/api/v1/health`
- [ ] Qdrant accessible: `curl http://localhost:6333/collections`
- [ ] Memory system works: `curl http://localhost:8000/api/v1/admin/memory/status`
- [ ] No OOM kills: `docker-compose logs rose | grep OOM` (empty result)
- [ ] Memory usage stable: `docker stats` (Rose < 80% of limit)
- [ ] Test conversation works: Open frontend and chat with Rose
- [ ] Memory persistence works: Restart containers and check memories retained

---

**Next Steps:**

1. Apply the fixed configurations
2. Run the rebuild and test commands above
3. Test memory system with diagnostic script: `python scripts/qdrant_diagnose.py`
4. Monitor for 24 hours to ensure stability
