# Build Production Docker Image

Build an optimized production Docker image for Rose.

## Pre-Build Checks

1. **Verify Environment**
   ```bash
   # Check .env file exists
   [ -f .env ] && echo "✅ .env found" || echo "❌ .env missing"

   # Verify API keys are set (without exposing values)
   grep -E "^GROQ_API_KEY=" .env > /dev/null && echo "✅ GROQ_API_KEY set" || echo "❌ GROQ_API_KEY missing"
   grep -E "^ELEVENLABS_API_KEY=" .env > /dev/null && echo "✅ ELEVENLABS_API_KEY set" || echo "❌ ELEVENLABS_API_KEY missing"
   ```

2. **Frontend Build Test**
   ```bash
   cd frontend
   npm run build
   cd ..
   ```
   - Should complete without errors
   - Creates `frontend/dist/` directory
   - Contains index.html and assets/

3. **Check Git Status**
   ```bash
   git status
   ```
   - Commit any important changes before building
   - Tag release version if needed

## Build Process

### Step 1: Clean Previous Builds
```bash
# Stop and remove old containers
docker-compose down

# Remove old images
docker rmi rose-rose:latest || true

# Clean Docker build cache (optional, for fresh build)
# docker builder prune -f
```

### Step 2: Build New Image
```bash
# Build with Docker Compose
docker-compose build rose

# This runs multi-stage build:
# 1. Frontend builder (Node.js 20) - builds React app
# 2. Python builder (UV package manager) - installs Python deps
# 3. Runtime stage (Python 3.12 slim) - combines frontend + backend
```

### Step 3: Monitor Build
Watch for these stages:
```
✅ [frontend-builder] npm ci
✅ [frontend-builder] npm run build (should take ~13s)
✅ [python-builder] uv sync (should take ~3min with CUDA libs)
✅ [stage-2] COPY frontend dist
✅ [stage-2] useradd appuser
✅ exporting to image
```

### Step 4: Verify Build
```bash
# Check image was created
docker images rose-rose:latest

# Should show:
# REPOSITORY   TAG      SIZE
# rose-rose    latest   ~3GB

# Check image layers
docker history rose-rose:latest --no-trunc | head -20
```

## Build Metrics

**Expected Build Times:**
- Frontend build: 10-20 seconds
- Python dependencies: 2-3 minutes (due to CUDA libraries)
- Image export: 2-4 minutes
- **Total**: ~7-11 minutes

**Expected Image Size:**
- Current: ~3GB (includes 2.5GB CUDA/PyTorch libraries)
- Optimized: ~300MB (after removing sentence-transformers)

## Post-Build Testing

### 1. Start Container
```bash
docker-compose up -d
```

### 2. Wait for Healthy Status
```bash
# Wait up to 30 seconds for health check
timeout=30
while [ $timeout -gt 0 ]; do
  status=$(docker inspect rose-rose-1 --format='{{.State.Health.Status}}')
  if [ "$status" = "healthy" ]; then
    echo "✅ Container is healthy"
    break
  fi
  echo "⏳ Waiting for container to be healthy... ($timeout seconds remaining)"
  sleep 2
  ((timeout-=2))
done
```

### 3. Test Endpoints
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Frontend
curl -I http://localhost:8000/

# API docs
curl -I http://localhost:8000/api/v1/docs
```

### 4. Check Logs
```bash
# Should see clean startup with no errors
docker-compose logs rose --tail 50

# Look for:
# ✅ Application startup complete
# ✅ Health check complete - all services healthy
# No ❌ or ERROR messages
```

### 5. Quick Voice Test
```bash
# Create session
curl -X POST http://localhost:8000/api/v1/session/start

# Should return session_id
```

## Build Optimization (Optional)

⚠️ **Known Issue**: Image is 3GB due to CUDA libraries from sentence-transformers

**To optimize** (reduces to ~300MB):
1. Switch from local embeddings to API-based (Groq or OpenAI)
2. Remove `sentence-transformers` from pyproject.toml
3. Rebuild image

See: `DEPLOYMENT_STATUS.md` → "CUDA Bloat Issue" section

## Troubleshooting

### Build Fails on Frontend Stage
```bash
# Test frontend build locally
cd frontend
rm -rf node_modules dist
npm ci
npm run build
```

### Build Fails on Python Dependencies
```bash
# Check pyproject.toml is valid
python -c "import tomli; tomli.load(open('pyproject.toml', 'rb'))"

# Test UV installation locally
pip install uv
uv sync
```

### Build Fails on COPY Step
```bash
# Verify dist directory exists
ls -la frontend/dist/

# Check Docker context
docker build -t test-build .
```

### Build is Slow
```bash
# Use Docker BuildKit for faster builds
export DOCKER_BUILDKIT=1
docker-compose build rose
```

## Build Report Format

```markdown
# 🏗️ Production Build Report

## Build Information
- Date: [timestamp]
- Git Commit: [hash]
- Git Branch: [branch]
- Builder: Docker Compose

## Build Stages
✅ Frontend Build: 13.2s
✅ Python Dependencies: 2m 52s
✅ Image Export: 3m 25s
⏱️ Total Time: 6m 30s

## Image Details
- Name: rose-rose:latest
- Size: 2.98 GB
- Layers: 30
- Platform: linux/amd64

## Post-Build Tests
✅ Container starts successfully
✅ Health check passes
✅ Frontend serves correctly
✅ API endpoints accessible
✅ No errors in logs

## Deployment Ready
🎉 Image is ready for deployment

## Next Steps
1. Tag image for production: `docker tag rose-rose:latest rose-rose:v1.0.0`
2. Push to registry (if using)
3. Deploy to Railway: `/deploy-railway`
4. Monitor deployment: `/check-health`

## Optimization Recommendations
⚠️ Consider removing CUDA dependencies to reduce image to ~300MB
   See: DEPLOYMENT_STATUS.md → CUDA Bloat Issue
```

## Production Tag

After successful build and testing:

```bash
# Tag with version number
docker tag rose-rose:latest rose-rose:v1.0.0

# Tag with date
docker tag rose-rose:latest rose-rose:$(date +%Y%m%d)

# List tagged images
docker images rose-rose
```

## Cleanup

```bash
# Remove dangling images
docker image prune -f

# Remove old build cache (if disk space needed)
docker builder prune -f
```
