# Rose Deployment Fixes Summary

**Date:** October 30, 2025
**Status:** In Progress - Docker Build Running

## Issues Identified and Fixed

### Critical Bugs Fixed

#### 1. API Base URL Mismatch (CRITICAL)
**Location:** [frontend/src/config/constants.ts:3](frontend/src/config/constants.ts#L3)

**Problem:**
```typescript
// BEFORE (BROKEN)
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
```
- Frontend was looking for backend on port 8080
- Backend actually runs on port 8000
- Result: "Cannot connect to Rose" error

**Fix:**
```typescript
// AFTER (FIXED)
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
```
- Uses relative path for same-origin requests
- Works in both dev (proxied) and production (Docker)
- No hardcoded ports!

#### 2. Docker Port Configuration Mismatch
**Location:** [docker-compose.yml](docker-compose.yml)

**Problem:**
- Dockerfile defaults to port 8080
- docker-compose mapped port 8000:8000
- Container would start on 8080 but mapping expected 8000

**Fix:**
```yaml
environment:
  - PORT=8000  # ← Added this
```
- Explicitly tells container to use port 8000
- Matches port mapping

#### 3. Docker Build Path Issue
**Location:** [frontend/vite.config.ts](frontend/vite.config.ts) & [Dockerfile](Dockerfile)

**Problem:**
- Vite built to `../src/ai_companion/interfaces/web/static/` (parent directory)
- Docker's multi-stage build couldn't access parent directories
- Build failed with "dist not found"

**Fix:**
```typescript
// vite.config.ts
const OUTPUT_DIR = process.env.DOCKER_BUILD
  ? 'dist'  // Docker: build to local dist
  : '../src/ai_companion/interfaces/web/static'  // Local: build to backend
```

```dockerfile
# Dockerfile
ENV DOCKER_BUILD=true
RUN npm run build
```
- Docker build outputs to container's /frontend/dist
- Local build outputs directly to backend static directory
- Dockerfile copies from /frontend/dist to final location

#### 4. Conflicting Process on Port 8000
**Problem:**
- Old Python dev server running on port 8000 (PID 42364)
- Blocked new deployments

**Fix:**
- Killed the process: `taskkill //PID 42364 //F`
- Port 8000 now available

## Architecture Overview

### Production (Docker) Flow
```
User Browser
    ↓
http://localhost:8000
    ↓
Rose Container (FastAPI)
    ├── Serves: Frontend static files (HTML, CSS, JS)
    └── Serves: API at /api/v1/*
    ↓
Qdrant Container
    └── Vector database on port 6333
```

### Development Flow
```
User Browser
    ↓
http://localhost:3000 (Vite Dev Server)
    ├── Serves: Frontend with hot reload
    └── Proxies /api/* requests to →
    ↓
http://localhost:8000 (FastAPI Server)
    └── Serves: API endpoints
    ↓
Qdrant (Docker)
    └── Vector database on port 6333
```

## Files Modified

### 1. Frontend Configuration
- `frontend/src/config/constants.ts` - Fixed API base URL
- `frontend/vite.config.ts` - Added conditional build output

### 2. Docker Configuration
- `docker-compose.yml` - Added PORT=8000 environment variable
- `Dockerfile` - Added DOCKER_BUILD=true for build step

### 3. No Backend Changes Needed!
- Backend code was already correct (thanks to earlier Uncle Bob cleanup)
- All constants properly configured
- Logging with emojis in place

## What's Running Now

### Docker Build Process
Currently building Docker image with:
1. ✅ Frontend built with fixed API URL
2. ✅ Frontend using correct dist directory for Docker
3. ⏳ Installing Python dependencies (large ML libraries)
4. ⏳ Copying frontend build to final location
5. ⏳ Creating production image

### Once Build Completes
```bash
# Start the stack
docker-compose up -d

# Access Rose
http://localhost:8000

# Check logs
docker-compose logs -f rose
```

## Testing Checklist

Once deployed, verify:

- [ ] Frontend loads without errors
- [ ] CSS styles applied correctly
- [ ] 3D scene renders properly
- [ ] Health check passes: `curl http://localhost:8000/api/v1/health`
- [ ] Voice button is interactive
- [ ] Can record audio
- [ ] Backend processes audio
- [ ] Receives voice response
- [ ] No console errors

## Environment Variables

Confirmed in `.env`:
- ✅ GROQ_API_KEY - Set
- ✅ ELEVENLABS_API_KEY - Set
- ✅ ELEVENLABS_VOICE_ID - Set
- ✅ QDRANT_URL - Set to http://localhost:6333

## Deployment Commands

### Docker Mode (Recommended)
```bash
# Build (currently running)
docker-compose build rose

# Start
docker-compose up -d

# View logs
docker-compose logs -f rose

# Stop
docker-compose down
```

### Local Dev Mode (Alternative)
```bash
# Start both servers
python scripts/run_dev_server.py

# Access
# Frontend: http://localhost:3000 (with hot reload)
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/api/v1/docs
```

### Production Build Mode (Alternative)
```bash
# Build and serve through FastAPI
python scripts/build_and_serve.py

# Access
http://localhost:8000
```

## Key Insights (Rubber Duck Analysis)

### Why It Failed Before
1. **Hardcoded Port Assumption**: Someone assumed 8080, but everything else used 8000
2. **Build Path Confusion**: Vite tried to build to parent directory in Docker context
3. **Port Conflict**: Old dev server blocking deployments

### The Uncle Bob Way
- **No Magic Numbers**: All ports/paths in constants
- **Single Source of Truth**: Configuration in one place
- **Proper Logging**: Emojis make debugging visual
- **Clean Separation**: Dev vs Docker build paths

### What We Learned
- Always use relative paths for API calls when possible
- Docker multi-stage builds can't access parent directories
- Environment variables solve dev vs prod differences
- Port conflicts are sneaky - always check with netstat

## Next Steps

1. ⏳ Wait for Docker build to complete (~5-10 minutes)
2. Start the stack with `docker-compose up -d`
3. Test the frontend at `http://localhost:8000`
4. Verify voice interaction works end-to-end
5. Check logs for any runtime issues

## Success Criteria

✅ Fixed API URL configuration
✅ Fixed Docker build paths
✅ Fixed port conflicts
✅ Frontend builds successfully
⏳ Docker image builds successfully
⏳ Container starts without errors
⏳ Frontend loads and connects to backend
⏳ Voice processing works end-to-end

---

**Built with ❤️ following Uncle Bob's Clean Code principles**

No magic numbers. Proper logging. Single responsibility. DRY. SOLID.

