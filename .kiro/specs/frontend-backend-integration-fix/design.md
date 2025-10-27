# Design Document: Frontend-Backend Integration Fix

## Overview

This design document outlines the technical solution for fixing the broken frontend-backend integration. The core issues are:

1. **Build Path Mismatch**: Vite outputs to wrong directory
2. **No Unified Server**: Frontend and backend run separately with no coordination
3. **Configuration Chaos**: Magic numbers, inconsistent paths, missing logs

### Design Principles

1. **🎯 Single Source of Truth**: All paths and ports defined once
2. **📝 Self-Documenting**: Emoji logs + named constants = no comments needed
3. **🔧 Developer Experience**: One command to rule them all
4. **🚀 Production Ready**: Same code path for dev and prod
5. **🛡️ Fail Fast**: Validate configuration on startup

## Architecture Changes

### Current (Broken) Architecture

```
Frontend (Vite) → Build to: ../src/ai_companion/interfaces/web/static/
                           ❌ But app.py looks for: frontend/build/
                           
Frontend Dev Server: http://localhost:3000
Backend API Server: ??? (not running)
```

### Fixed Architecture

```
Frontend (Vite) → Build to: src/ai_companion/interfaces/web/static/
                           ✅ Matches app.py expectation
                           
Development Mode:
  - Vite Dev Server: http://localhost:3000 (proxies API to :8000)
  - FastAPI Server: http://localhost:8000 (serves API + CORS)
  
Production Mode:
  - FastAPI Server: http://localhost:8000 (serves static + API)
```

## Component Design

### 1. Configuration Constants Module

**File**: `src/ai_companion/config/server_config.py`

**Purpose**: Centralize all magic numbers into named constants with emoji documentation.


**Implementation**:
```python
# 🌐 Network Configuration
WEB_SERVER_HOST = "0.0.0.0"  # Listen on all interfaces
WEB_SERVER_PORT = 8000  # Main web interface port
DEV_FRONTEND_PORT = 3000  # Vite dev server port

# 📁 Path Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
FRONTEND_SOURCE_DIR = PROJECT_ROOT / "frontend"
FRONTEND_BUILD_DIR = PROJECT_ROOT / "src" / "ai_companion" / "interfaces" / "web" / "static"

# ⏱️ Timeout Configuration
API_REQUEST_TIMEOUT_SECONDS = 60
WORKFLOW_TIMEOUT_SECONDS = 55  # Slightly less than API timeout
HEALTH_CHECK_TIMEOUT_SECONDS = 5

# 📦 File Size Limits
MAX_AUDIO_FILE_SIZE_MB = 10
MAX_AUDIO_FILE_SIZE_BYTES = MAX_AUDIO_FILE_SIZE_MB * 1024 * 1024

# 🔄 Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE = 10

# 🎨 Asset Configuration
STATIC_ASSET_CACHE_SECONDS = 31536000  # 1 year for immutable assets
HTML_CACHE_SECONDS = 300  # 5 minutes for HTML
API_CACHE_SECONDS = 0  # No cache for API responses

# 🧹 Cleanup Configuration
AUDIO_CLEANUP_MAX_AGE_HOURS = 24
AUDIO_CLEANUP_INTERVAL_HOURS = 1

# 🌍 CORS Configuration
DEV_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

### 2. Vite Configuration Fix

**File**: `frontend/vite.config.ts`

**Changes**:
- Fix output directory to match backend expectation
- Configure proxy for API requests in dev mode
- Add emoji logs for build events

**Implementation**:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// 🎯 Build output matches backend static directory
const OUTPUT_DIR = path.resolve(__dirname, '../src/ai_companion/interfaces/web/static')

// 🌐 API proxy configuration for development
const API_PROXY_TARGET = 'http://localhost:8000'

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'build-logger',
      buildStart() {
        console.log('🎨 Starting frontend build...')
      },
      buildEnd() {
        console.log(`✅ Build complete! Output: ${OUTPUT_DIR}`)
      }
    }
  ],
  build: {
    outDir: OUTPUT_DIR,
    emptyOutDir: true,
    // ... rest of config
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: API_PROXY_TARGET,
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
```

### 3. FastAPI Server Updates

**File**: `src/ai_companion/interfaces/web/app.py`

**Changes**:
- Use configuration constants
- Add emoji logging
- Fix static file path
- Improve error messages

**Key Updates**:
```python
from ai_companion.config.server_config import (
    FRONTEND_BUILD_DIR,
    WEB_SERVER_PORT,
    DEV_ALLOWED_ORIGINS,
    STATIC_ASSET_CACHE_SECONDS,
)

# 🎨 Frontend static files
if FRONTEND_BUILD_DIR.exists():
    logger.info("✅ Frontend build found", path=str(FRONTEND_BUILD_DIR))
    app.mount("/assets", StaticFiles(directory=FRONTEND_BUILD_DIR / "assets"), name="assets")
else:
    logger.error("❌ Frontend build not found", expected_path=str(FRONTEND_BUILD_DIR))
```

### 4. Development Server Script

**File**: `scripts/run_dev_server.py`

**Purpose**: Single command to start both frontend and backend in development mode.

**Implementation**:
```python
#!/usr/bin/env python3
"""
🚀 Development Server Launcher

Starts both the Vite dev server (frontend) and FastAPI server (backend)
for local development with hot reload.
"""
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def start_backend():
    """🔌 Start FastAPI backend server"""
    print("🔌 Starting backend server on http://localhost:8000...")
    backend_process = subprocess.Popen(
        ["uvicorn", "ai_companion.interfaces.web.app:app", "--reload", "--port", "8000"],
        cwd=PROJECT_ROOT,
    )
    return backend_process

def start_frontend():
    """🎨 Start Vite frontend dev server"""
    print("🎨 Starting frontend dev server on http://localhost:3000...")
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=PROJECT_ROOT / "frontend",
    )
    return frontend_process

def main():
    print("🚀 Starting Rose development servers...")
    
    backend = start_backend()
    time.sleep(2)  # Give backend time to start
    
    frontend = start_frontend()
    
    print("\n✅ Development servers running!")
    print("   🎨 Frontend: http://localhost:3000")
    print("   🔌 Backend:  http://localhost:8000")
    print("   📚 API Docs: http://localhost:8000/api/v1/docs")
    print("\n   Press Ctrl+C to stop all servers\n")
    
    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
        backend.terminate()
        frontend.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
```

### 5. Production Build Script

**File**: `scripts/build_and_serve.py`

**Purpose**: Build frontend and start production server.

**Implementation**:
```python
#!/usr/bin/env python3
"""
📦 Production Build and Serve

Builds the frontend and starts the FastAPI server in production mode.
"""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def build_frontend():
    """🎨 Build frontend for production"""
    print("🎨 Building frontend...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=PROJECT_ROOT / "frontend",
    )
    if result.returncode != 0:
        print("❌ Frontend build failed!")
        sys.exit(1)
    print("✅ Frontend build complete!")

def start_production_server():
    """🚀 Start production server"""
    print("🚀 Starting production server on http://localhost:8000...")
    subprocess.run(
        ["uvicorn", "ai_companion.interfaces.web.app:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=PROJECT_ROOT,
    )

def main():
    print("📦 Building Rose for production...")
    build_frontend()
    start_production_server()

if __name__ == "__main__":
    main()
```

### 6. Frontend API Client Updates

**File**: `frontend/src/services/apiClient.ts`

**Changes**:
- Use environment variable for base URL
- Add emoji logging
- Improve error messages

**Implementation**:
```typescript
// 🌐 API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    console.log('🔌 Initializing API client:', API_BASE_URL)
    
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 60000,
    })
    
    // 📊 Request logging
    this.client.interceptors.request.use(config => {
      console.log('📤 API Request:', config.method?.toUpperCase(), config.url)
      return config
    })
    
    // 📊 Response logging
    this.client.interceptors.response.use(
      response => {
        console.log('✅ API Response:', response.config.url, response.status)
        return response
      },
      error => {
        console.error('❌ API Error:', error.config?.url, error.message)
        throw error
      }
    )
  }
}
```

### 7. Health Check Implementation

**File**: `frontend/src/hooks/useHealthCheck.ts`

**Purpose**: Verify backend connectivity on app startup.

**Implementation**:
```typescript
export const useHealthCheck = () => {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        console.log('🏥 Checking backend health...')
        const response = await apiClient.checkHealth()
        console.log('✅ Backend healthy:', response)
        setIsHealthy(true)
      } catch (err) {
        console.error('❌ Backend health check failed:', err)
        setError('Cannot connect to Rose. Please ensure the server is running.')
        setIsHealthy(false)
      }
    }

    checkHealth()
  }, [])

  return { isHealthy, error }
}
```

### 8. Development Documentation

**File**: `DEVELOPMENT.md`

**Content**:
```markdown
# 🚀 Rose Development Guide

## Quick Start

### Development Mode (Hot Reload)

```bash
# 🔧 Install dependencies
cd frontend && npm install && cd ..
uv sync

# 🚀 Start both servers
python scripts/run_dev_server.py
```

This starts:
- 🎨 Frontend: http://localhost:3000 (Vite dev server with hot reload)
- 🔌 Backend: http://localhost:8000 (FastAPI with auto-reload)
- 📚 API Docs: http://localhost:8000/api/v1/docs

### Production Mode

```bash
# 📦 Build and serve
python scripts/build_and_serve.py
```

This:
1. 🎨 Builds frontend to `src/ai_companion/interfaces/web/static/`
2. 🚀 Starts FastAPI server serving both static files and API

## Troubleshooting

### ❌ "Cannot connect to Rose"

**Problem**: Frontend can't reach backend API

**Solutions**:
1. ✅ Ensure backend is running on port 8000
2. ✅ Check `VITE_API_BASE_URL` in `frontend/.env`
3. ✅ Verify CORS settings in backend

### ❌ "Styles not loading"

**Problem**: CSS/3D assets not loading

**Solutions**:
1. ✅ Run `npm run build` in frontend directory
2. ✅ Verify build output in `src/ai_companion/interfaces/web/static/`
3. ✅ Check browser console for 404 errors

### ❌ "Voice processing error"

**Problem**: Microphone or API issues

**Solutions**:
1. ✅ Allow microphone access in browser
2. ✅ Check backend logs for errors
3. ✅ Verify Groq API key is set
```

## Error Handling Strategy

### Frontend Error Messages

```typescript
// 🎯 User-friendly error messages
const ERROR_MESSAGES = {
  BACKEND_UNREACHABLE: '🔌 Cannot connect to Rose. Please ensure the server is running.',
  MICROPHONE_DENIED: '🎤 Microphone access denied. Please allow microphone access in your browser settings.',
  VOICE_PROCESSING_FAILED: '🎤 I couldn\'t hear that clearly. Could you try again?',
  AUDIO_PLAYBACK_FAILED: '🔊 Failed to play audio response. Please check your speakers.',
  SESSION_EXPIRED: '⏱️ Your session has expired. Please refresh the page.',
}
```

### Backend Error Logging

```python
# 🎯 Structured error logging with emojis
logger.error("❌ Voice processing failed", 
    error=str(e),
    session_id=session_id,
    exc_info=True
)
```

## Testing Strategy

### Manual Testing Checklist

1. ✅ Frontend loads without errors
2. ✅ All CSS styles applied correctly
3. ✅ 3D scene renders properly
4. ✅ Voice button responds to clicks
5. ✅ Microphone permission requested
6. ✅ Voice recording works
7. ✅ Backend processes voice input
8. ✅ Audio response plays correctly
9. ✅ Error messages display properly
10. ✅ Health check passes

### Automated Tests

```bash
# 🧪 Run frontend tests
cd frontend && npm test

# 🧪 Run backend tests
pytest tests/
```

## Configuration Reference

### Environment Variables

**Frontend** (`frontend/.env`):
```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

**Backend** (`.env`):
```bash
# Already configured in existing .env
GROQ_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here
```

## Deployment

See `docs/DEPLOYMENT.md` for production deployment instructions.
```

## Implementation Order

1. **Phase 1: Configuration** (30 min)
   - Create `server_config.py` with all constants
   - Update Vite config with correct paths
   - Update frontend `.env` file

2. **Phase 2: Backend Updates** (30 min)
   - Update `app.py` to use config constants
   - Add emoji logging throughout
   - Fix static file serving path

3. **Phase 3: Development Scripts** (30 min)
   - Create `run_dev_server.py`
   - Create `build_and_serve.py`
   - Make scripts executable

4. **Phase 4: Frontend Updates** (30 min)
   - Update API client with logging
   - Add health check hook
   - Update error messages

5. **Phase 5: Documentation** (30 min)
   - Create `DEVELOPMENT.md`
   - Update README with quick start
   - Add troubleshooting guide

6. **Phase 6: Testing** (30 min)
   - Test development mode
   - Test production build
   - Verify all features work

## Success Criteria

✅ Single command starts both servers  
✅ Frontend connects to backend successfully  
✅ Voice processing works end-to-end  
✅ All styles and 3D assets load correctly  
✅ Error messages are clear and actionable  
✅ All magic numbers replaced with named constants  
✅ All logs include emoji indicators  
✅ Documentation is complete and accurate
