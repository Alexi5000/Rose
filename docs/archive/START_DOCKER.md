# 🚀 Start Rose Application - Step by Step

## Issue Identified
❌ Docker Desktop is not running
❌ Backend containers are offline
❌ Voice button cannot connect to API

## Solution

### Step 1: Start Docker Desktop ⏱️ 30 seconds

**Method 1 - Windows Start Menu:**
1. Press `Windows` key
2. Type: `Docker Desktop`
3. Press `Enter`
4. Wait for icon in system tray

**Method 2 - Command Line:**
```powershell
# Open PowerShell as Administrator
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

**✅ Confirmation:**
- Docker icon appears in system tray (bottom right)
- Icon stops animating and shows "Docker Desktop is running"

### Step 2: Start Rose Containers ⏱️ 1-2 minutes

```bash
# In Git Bash or PowerShell
cd c:\TechTide\Apps\Rose

# Start containers in background
docker-compose up -d
```

**Expected Output:**
```
🔄 Creating network rose_default
🔄 Creating volume rose_qdrant_data
🔄 Creating volume rose_rose_data
✅ Container rose-qdrant-1  Started
✅ Container rose-rose-1  Started
```

### Step 3: Verify Health ⏱️ 10 seconds

```bash
# Check containers are running
docker-compose ps

# Should show:
# NAME            STATUS
# rose-qdrant-1   Up (healthy)
# rose-rose-1     Up (healthy)

# Test backend API
curl http://localhost:8000/api/v1/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "groq": "connected",
    "qdrant": "connected",
    "elevenlabs": "connected",
    "sqlite": "connected"
  }
}
```

### Step 4: Test Voice Interaction ⏱️ 30 seconds

1. **Open browser**: http://localhost:8000
2. **Allow microphone** when prompted
3. **Press and HOLD Space bar**
4. **Say**: "Hello Rose, I'm feeling sad"
5. **Release Space bar**
6. **Wait**: 5-10 seconds for response

**✅ Success Indicators:**
- Button shows "Listening..." while holding Space
- Button shows "Processing your message..." after release
- You hear Rose's voice response
- Button returns to idle state

---

## 🚨 Troubleshooting

### Docker Desktop Won't Start

**Error**: "Docker Desktop is starting..."
- **Wait**: Can take 1-2 minutes on first start
- **Check**: System resources (needs 2GB RAM, 2GB disk)
- **Restart**: Close and reopen Docker Desktop

**Error**: "WSL 2 installation is incomplete"
```powershell
# Install WSL 2
wsl --install
# Restart computer
```

### Containers Won't Start

**Error**: "port 8000 is already allocated"
```bash
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill //PID <PID> //F

# Retry
docker-compose up -d
```

**Error**: "port 6333 is already allocated"
```bash
# Stop old Qdrant container
docker stop rose-qdrant
docker rm rose-qdrant

# Retry
docker-compose up -d
```

### Health Check Fails

**Error**: API returns 503 or connection refused
```bash
# Check logs for errors
docker-compose logs rose --tail 50

# Common issues:
# - Missing .env file
# - Invalid API keys
# - Services still starting (wait 30s)
```

### Voice Still Doesn't Work

**After containers are running:**

1. **Check browser console** (F12 → Console):
   - Should see: "🔌 Initializing API client"
   - Should NOT see: "❌ Backend unreachable"

2. **Verify microphone permission**:
   - Click padlock in address bar
   - Ensure "Microphone" is "Allow"
   - Refresh page

3. **Test press-and-hold pattern**:
   - HOLD Space (don't click once)
   - Speak while holding
   - RELEASE Space (this sends the request)

---

## 📊 Quick Diagnostic Commands

**Is Docker Running?**
```bash
docker ps
# Should list containers, not error
```

**Are Containers Running?**
```bash
docker-compose ps
# Should show "Up" status
```

**Is Backend Accessible?**
```bash
curl http://localhost:8000/api/v1/health
# Should return JSON with "healthy"
```

**Are There Recent Errors?**
```bash
docker-compose logs rose --tail 50 | grep -E "ERROR|❌"
# Should be empty or minimal
```

---

## ✅ Success Checklist

Before testing voice:
- [ ] Docker Desktop icon in system tray (running)
- [ ] `docker ps` shows 2 containers running
- [ ] `curl localhost:8000/api/v1/health` returns healthy
- [ ] Browser opens http://localhost:8000 successfully
- [ ] Microphone permission granted
- [ ] Understand press-and-hold pattern

---

## 🎉 You're Ready!

Once all containers are running:

1. Open: http://localhost:8000
2. Press and HOLD Space
3. Say: "Hello Rose"
4. Release Space
5. Wait for response

**Total time from cold start**: ~3 minutes

---

**Need Help?**
- Check Docker Desktop logs (Settings → Troubleshoot → View Logs)
- Run: `docker-compose logs -f rose` to watch live logs
- Visit: http://localhost:8000/api/v1/docs for API testing

**Last Updated**: October 30, 2025
