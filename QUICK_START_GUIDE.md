# 🚀 Rose the Healer Shaman - Quick Start Guide

**Last Updated:** October 30, 2025  
**Estimated Setup Time:** 15-20 minutes

This guide will get you from zero to a running Rose AI companion in under 20 minutes.

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Python 3.12+** installed ([Download](https://www.python.org/downloads/))
- [ ] **Node.js 18+** with npm installed ([Download](https://nodejs.org/))
- [ ] **uv** package manager installed ([Install Guide](https://docs.astral.sh/uv/getting-started/installation/))
- [ ] **Docker** installed (for Qdrant) ([Download](https://www.docker.com/get-started))
- [ ] **API Keys** ready:
  - Groq API key ([Get it here](https://console.groq.com/keys))
  - ElevenLabs API key ([Get it here](https://elevenlabs.io/))
  - Qdrant Cloud URL (optional, or use local Docker)

---

## 🎯 Step-by-Step Setup

### Step 1: Clone and Navigate (2 minutes)

```bash
# If you haven't cloned yet
git clone <your-repo-url>
cd ai-companion

# Verify you're in the right directory
ls -la  # Should see: README.md, pyproject.toml, frontend/, src/, etc.
```

### Step 2: Run Diagnostic Tool (1 minute)

```bash
# Check what needs to be set up
python scripts/diagnose_deployment.py
```

This will show you exactly what's missing. Don't worry if things fail - we'll fix them!

### Step 3: Auto-Fix Common Issues (5 minutes)

```bash
# Automatically fix configuration issues
python scripts/fix_deployment_issues.py

# Or preview what would be fixed
python scripts/fix_deployment_issues.py --dry-run
```

This will:
- ✅ Fix Qdrant URL for local development
- ✅ Install Python dependencies
- ✅ Install frontend dependencies
- ✅ Build frontend for production
- ✅ Fix Docker Compose configuration
- ✅ Create memory directories

### Step 4: Configure Environment Variables (3 minutes)

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
# Use your favorite editor (nano, vim, code, notepad, etc.)
nano .env  # or: code .env
```

**Required variables to set:**
```env
GROQ_API_KEY="gsk_YOUR_KEY_HERE"
ELEVENLABS_API_KEY="sk_YOUR_KEY_HERE"
ELEVENLABS_VOICE_ID="YOUR_VOICE_ID_HERE"
QDRANT_URL="http://localhost:6333"  # Already set by auto-fix
```

**How to get API keys:**
1. **Groq**: Sign up at https://console.groq.com/ → API Keys → Create
2. **ElevenLabs**: Sign up at https://elevenlabs.io/ → Profile → API Keys
3. **Voice ID**: Browse https://elevenlabs.io/voice-library → Pick a warm, calming voice → Copy ID

### Step 5: Start Qdrant (2 minutes)

```bash
# Option 1: Docker (Recommended for local dev)
docker run -d -p 6333:6333 -v $(pwd)/long_term_memory:/qdrant/storage qdrant/qdrant:latest

# Option 2: Docker Compose (for full stack)
docker compose up -d qdrant

# Verify Qdrant is running
curl http://localhost:6333/health
# Should return: {"title":"qdrant - vector search engine","version":"..."}
```

### Step 6: Verify Setup (1 minute)

```bash
# Run diagnostic again to verify everything is ready
python scripts/diagnose_deployment.py
```

You should see all green checkmarks ✅!

### Step 7: Start Development Server (2 minutes)

```bash
# Start both frontend and backend with hot reload
python scripts/run_dev_server.py
```

This will:
- 🔌 Start FastAPI backend on http://localhost:8000
- 🎨 Start Vite frontend on http://localhost:3000
- 📚 Serve API docs at http://localhost:8000/api/v1/docs

**Wait for these messages:**
```
✅ Backend is ready!
✅ Development servers running!

   🎨 Frontend: http://localhost:3000
   🔌 Backend:  http://localhost:8000
   📚 API Docs: http://localhost:8000/api/v1/docs

   Press Ctrl+C to stop all servers
```

### Step 8: Test Rose! (5 minutes)

1. **Open your browser** to http://localhost:3000
2. **Wait for the scene to load** (you'll see a beautiful ice cave with aurora)
3. **Click and hold the voice button** (or press Space)
4. **Speak your message** (e.g., "Hi Rose, I'm feeling anxious today")
5. **Release to send**
6. **Listen to Rose's response** (both text and audio)

**First-time tips:**
- Grant microphone permissions when prompted
- Speak clearly and wait for the "listening" indicator
- Rose remembers your conversation across sessions
- Try asking about grief, healing, or emotional support

---

## 🎨 Production Build (Optional)

If you want to test the production build:

```bash
# Build frontend and start production server
python scripts/build_and_serve.py
```

This serves the app at http://localhost:8000 (single port, no hot reload).

---

## 🐳 Docker Deployment (Optional)

To run the entire stack in Docker:

```bash
# Build and start all services
docker compose up --build

# Or use make commands
make rose-build
make rose-start

# Access at http://localhost:8000
```

**Note:** Docker deployment uses `QDRANT_URL=http://qdrant:6333` automatically.

---

## 🔧 Troubleshooting

### "Failed to connect to Qdrant"

**Cause:** Qdrant not running or wrong URL

**Fix:**
```bash
# Check if Qdrant is running
docker ps | grep qdrant

# If not running, start it
docker run -d -p 6333:6333 qdrant/qdrant:latest

# Verify connectivity
curl http://localhost:6333/health
```

### "Frontend not found"

**Cause:** Frontend not built

**Fix:**
```bash
cd frontend
npm run build
cd ..
```

### "Module not found" errors

**Cause:** Dependencies not installed

**Fix:**
```bash
# Python dependencies
uv sync

# Frontend dependencies
cd frontend && npm install && cd ..
```

### "Audio file too large"

**Cause:** Recording too long (>10MB)

**Fix:** Keep recordings under 2 minutes. The app will automatically stop at 2 minutes.

### "Rate limit exceeded"

**Cause:** Too many requests (10/minute limit)

**Fix:** Wait a minute before trying again. This protects the API from abuse.

### Port already in use

**Cause:** Another process using port 8000 or 3000

**Fix:**
```bash
# Find and kill process on port 8000
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:8000 | xargs kill -9
```

---

## 📊 Verification Checklist

After setup, verify these work:

- [ ] Diagnostic tool shows all green ✅
- [ ] Dev server starts without errors
- [ ] Frontend loads at http://localhost:3000
- [ ] Backend health check passes at http://localhost:8000/api/v1/health
- [ ] Voice button appears and is clickable
- [ ] Microphone permission granted
- [ ] Can record and send voice message
- [ ] Rose responds with text and audio
- [ ] Audio plays automatically
- [ ] Session persists across page refreshes

---

## 🎯 Next Steps

Once everything is working:

1. **Explore the API docs** at http://localhost:8000/api/v1/docs
2. **Read the architecture** in `DEPLOYMENT_READINESS_ANALYSIS.md`
3. **Run the tests** with `uv run pytest`
4. **Check code coverage** with `uv run pytest --cov=src --cov-report=html`
5. **Deploy to production** (see Railway/Render guides in docs/)

---

## 🆘 Still Having Issues?

1. **Check the logs** - Look for error messages in the terminal
2. **Run diagnostic** - `python scripts/diagnose_deployment.py`
3. **Read the analysis** - `DEPLOYMENT_READINESS_ANALYSIS.md`
4. **Check GitHub issues** - Someone may have had the same problem
5. **Ask for help** - Create a GitHub issue with:
   - Output of diagnostic tool
   - Error messages from logs
   - Your OS and Python version
   - Steps you've tried

---

## 📚 Additional Resources

- **Full Documentation**: See `README.md`
- **Development Guide**: See `DEVELOPMENT.md`
- **Architecture Details**: See `docs/ARCHITECTURE.md`
- **API Reference**: http://localhost:8000/api/v1/docs (when running)
- **Testing Guide**: See `tests/README.md`

---

**🌹 Welcome to Rose! May your healing journey be gentle and transformative.**
