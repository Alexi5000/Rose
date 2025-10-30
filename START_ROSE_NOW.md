# 🌹 START ROSE NOW - Simple Guide

**Last Updated:** October 30, 2025

## 🎯 The Simplest Way to Start Rose

### One Command to Rule Them All:

```bash
python scripts/deploy_rose_ultimate.py
```

That's it! This script will:
1. ✅ Check prerequisites
2. ✅ Verify .env configuration
3. ✅ Stop old containers
4. ✅ Clean artifacts
5. ✅ Build fresh containers
6. ✅ Start everything
7. ✅ Verify health
8. ✅ Show you how to access Rose

## 📋 Before You Run

### 1. Make sure you have .env file:
```bash
# If you don't have .env, copy the example:
copy .env.example .env

# Then edit .env and add your API keys:
# - GROQ_API_KEY
# - ELEVENLABS_API_KEY
# - ELEVENLABS_VOICE_ID
```

### 2. Make sure Docker is running:
- Open Docker Desktop
- Wait for it to say "Docker Desktop is running"

## 🚀 After Deployment

### Access Rose:
```
http://localhost:8000
```

### View Logs:
```bash
docker-compose logs -f rose
```

### Stop Rose:
```bash
docker-compose down
```

### Restart Rose:
```bash
docker-compose up -d
```

## 🔧 Troubleshooting

### If deployment fails:

1. **Check Docker is running:**
   ```bash
   docker ps
   ```

2. **Check .env file exists:**
   ```bash
   dir .env
   ```

3. **Check logs:**
   ```bash
   docker-compose logs rose
   ```

4. **Try manual cleanup:**
   ```bash
   docker-compose down
   docker system prune -f
   python scripts/deploy_rose_ultimate.py
   ```

### If Rose won't start:

1. **Check API keys are valid:**
   - GROQ_API_KEY: https://console.groq.com/
   - ELEVENLABS_API_KEY: https://elevenlabs.io/

2. **Check Qdrant is running:**
   ```bash
   curl http://localhost:6333
   ```

3. **Check port 8000 is free:**
   ```bash
   netstat -ano | findstr :8000
   ```

## 📊 What's Running?

After successful deployment:

| Service | Port | URL |
|---------|------|-----|
| Rose (Frontend + Backend) | 8000 | http://localhost:8000 |
| Qdrant (Vector DB) | 6333 | http://localhost:6333 |

## 🎤 Using Rose

1. **Open browser:** http://localhost:8000
2. **Click and hold** the voice button
3. **Speak** your message
4. **Release** to send
5. **Listen** to Rose's response

## 💡 Tips

- **First response may be slow** (loading models)
- **Speak clearly** for best transcription
- **Check your microphone** permissions in browser
- **Use headphones** to avoid echo

## 🆘 Need Help?

1. Check **DEPLOYMENT_COMPLETE_FINAL.md** for detailed info
2. Check **DEPLOYMENT_VERIFICATION_PLAN.md** for troubleshooting
3. Check logs: `docker-compose logs rose`
4. Check this file for common issues

---

**Built with ❤️ following Uncle Bob's Clean Code principles**

🌹 Rose is ready to heal! 🌹
