# 🌹 How to Start Rose - Complete Checklist

**Last Updated:** October 30, 2025  
**Estimated Time:** 5 minutes

---

## ✅ Pre-flight Checklist

Before starting Rose, verify these are ready:

- [ ] Docker Desktop is installed and running
- [ ] You have API keys in `.env` file
- [ ] You're in the project root directory (`C:\TechTide\Apps\Rose`)

---

## 🚀 Startup Sequence

### Step 1: Start Docker Desktop (2 minutes)

1. **Open Docker Desktop** from Start Menu or Desktop
2. **Wait for it to start** - Look for the whale icon in system tray
3. **Verify it's running:**
   ```powershell
   docker ps
   ```
   Should show a table (even if empty), not an error

### Step 2: Start Qdrant (1 minute)

```powershell
# Start Qdrant vector database
docker run -d -p 6333:6333 -v ${PWD}/long_term_memory:/qdrant/storage --name rose-qdrant qdrant/qdrant:latest
```

**Verify Qdrant is running:**
```powershell
# Check if container is running
docker ps | findstr qdrant

# Test connectivity
curl http://localhost:6333/health
```

Should return: `{"title":"qdrant - vector search engine","version":"..."}`

### Step 3: Start Rose Development Servers (2 minutes)

```powershell
# Start both frontend and backend
python scripts/run_dev_server.py
```

**Wait for these messages:**
```
✅ Backend is ready!
✅ Development servers running!

   🎨 Frontend: http://localhost:3000
   🔌 Backend:  http://localhost:8000
   📚 API Docs: http://localhost:8000/api/v1/docs

   Press Ctrl+C to stop all servers
```

### Step 4: Open Rose in Browser

1. **Open your browser** to http://localhost:3000
2. **Wait for scene to load** (beautiful ice cave with aurora)
3. **Grant microphone permission** when prompted
4. **Click the voice button** and start talking to Rose!

---

## 🔧 Troubleshooting

### "Docker Desktop is not running"

**Symptoms:**
```
error during connect: open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified
```

**Fix:**
1. Open Docker Desktop from Start Menu
2. Wait 30-60 seconds for it to fully start
3. Look for whale icon in system tray (should be steady, not animated)
4. Try `docker ps` again

### "Port 6333 is already in use"

**Symptoms:**
```
Error starting userland proxy: listen tcp4 0.0.0.0:6333: bind: Only one usage of each socket address
```

**Fix:**
```powershell
# Stop existing Qdrant container
docker stop rose-qdrant
docker rm rose-qdrant

# Start fresh
docker run -d -p 6333:6333 -v ${PWD}/long_term_memory:/qdrant/storage --name rose-qdrant qdrant/qdrant:latest
```

### "Cannot connect to Qdrant"

**Symptoms:**
```
❌ Qdrant Connectivity
   Cannot connect to Qdrant: ...
```

**Fix:**
```powershell
# Check if Qdrant is running
docker ps | findstr qdrant

# If not running, start it
docker start rose-qdrant

# If doesn't exist, create it
docker run -d -p 6333:6333 -v ${PWD}/long_term_memory:/qdrant/storage --name rose-qdrant qdrant/qdrant:latest

# Test connectivity
curl http://localhost:6333/health
```

### "Port 8000 is already in use"

**Symptoms:**
```
Error: [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000)
```

**Fix:**
```powershell
# Find what's using port 8000
netstat -ano | findstr ":8000"

# Kill the process (replace <PID> with actual process ID)
taskkill /PID <PID> /F

# Or use a different port
$env:PORT=8001
python scripts/run_dev_server.py
```

### "Port 3000 is already in use"

**Symptoms:**
```
Port 3000 is in use, trying another one...
```

**Fix:**
```powershell
# Find what's using port 3000
netstat -ano | findstr ":3000"

# Kill the process
taskkill /PID <PID> /F
```

### "Module not found" errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'langchain'
```

**Fix:**
```powershell
# Reinstall Python dependencies
uv sync

# Verify installation
python -c "import langchain; print('OK')"
```

### "Frontend not loading"

**Symptoms:**
- Blank page at http://localhost:3000
- Console errors about missing files

**Fix:**
```powershell
# Rebuild frontend
cd frontend
npm run build
cd ..

# Restart dev server
python scripts/run_dev_server.py
```

---

## 🛑 How to Stop Rose

### Stop Development Servers
```powershell
# Press Ctrl+C in the terminal where dev server is running
# Wait for graceful shutdown message
```

### Stop Qdrant
```powershell
# Stop but keep data
docker stop rose-qdrant

# Stop and remove container (data is preserved in volume)
docker stop rose-qdrant
docker rm rose-qdrant
```

### Stop Docker Desktop
```powershell
# Right-click whale icon in system tray → Quit Docker Desktop
```

---

## 📊 Health Check Commands

Run these to verify everything is working:

```powershell
# 1. Check Docker is running
docker ps

# 2. Check Qdrant is running
docker ps | findstr qdrant
curl http://localhost:6333/health

# 3. Check backend is running
curl http://localhost:8000/api/v1/health

# 4. Check frontend is running
curl http://localhost:3000

# 5. Run full diagnostic
python scripts/diagnose_deployment.py
```

---

## 🎯 Quick Start (All-in-One)

If everything is already set up, just run:

```powershell
# 1. Start Docker Desktop (manually)
# 2. Start Qdrant
docker start rose-qdrant || docker run -d -p 6333:6333 -v ${PWD}/long_term_memory:/qdrant/storage --name rose-qdrant qdrant/qdrant:latest

# 3. Start Rose
python scripts/run_dev_server.py

# 4. Open http://localhost:3000
```

---

## 📝 Daily Workflow

### Morning Startup
```powershell
# 1. Open Docker Desktop
# 2. Start Qdrant
docker start rose-qdrant

# 3. Start Rose
python scripts/run_dev_server.py

# 4. Open http://localhost:3000
```

### Evening Shutdown
```powershell
# 1. Stop dev server (Ctrl+C)
# 2. Stop Qdrant
docker stop rose-qdrant

# 3. Quit Docker Desktop (optional)
```

---

## 🆘 Still Having Issues?

1. **Run diagnostic:**
   ```powershell
   python scripts/diagnose_deployment.py
   ```

2. **Check logs:**
   - Dev server output in terminal
   - Docker logs: `docker logs rose-qdrant`
   - Browser console (F12)

3. **Try auto-fix:**
   ```powershell
   python scripts/fix_deployment_issues.py
   ```

4. **Read detailed guides:**
   - `QUICK_START_GUIDE.md` - Full setup guide
   - `DEPLOYMENT_READINESS_ANALYSIS.md` - Technical details
   - `DEPLOYMENT_COMPLETE.md` - Completion report

---

**🌹 Ready to start your healing journey with Rose!**
