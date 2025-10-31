# Check System Health

Verify all services and components are healthy and properly configured.

## Health Checks to Perform

1. **Docker Containers**
   ```bash
   docker-compose ps
   ```
   - Verify `rose-rose-1` is Up (healthy)
   - Verify `rose-qdrant-1` is Up
   - Check ports 8000 and 6333 are mapped correctly

2. **Backend API Health**
   ```bash
   curl -s http://localhost:8000/api/v1/health | jq
   ```
   Expected response:
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

3. **API Documentation**
   ```bash
   curl -I http://localhost:8000/api/v1/docs
   ```
   - Should return 200 OK
   - Swagger UI should be accessible

4. **Frontend Serving**
   ```bash
   curl -I http://localhost:8000/
   ```
   - Should return 200 OK
   - Content-Type: text/html

5. **Static Assets**
   ```bash
   # Test CSS
   curl -I "http://localhost:8000/assets/index-*.css"

   # Test JS
   curl -I "http://localhost:8000/assets/index-*.js"
   ```
   - Should return 200 OK
   - Proper cache headers

6. **Environment Variables**
   Check critical env vars are set (without exposing values):
   ```bash
   docker exec rose-rose-1 env | grep -E "(GROQ|ELEVENLABS|QDRANT)" | sed 's/=.*/=***/'
   ```
   - GROQ_API_KEY=***
   - ELEVENLABS_API_KEY=***
   - ELEVENLABS_VOICE_ID=***

7. **Recent Errors**
   ```bash
   docker-compose logs rose --tail 200 | grep -E "(ERROR|❌|error|failed)"
   ```
   - Should be empty or minimal
   - Investigate any errors found

8. **Memory Usage**
   ```bash
   docker stats rose-rose-1 --no-stream
   ```
   - Should be < 512MB for Railway compatibility
   - Note if approaching limits

## Report Format

Provide a summary with emoji indicators:

```
🏥 Rose Health Check Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Containers: Running (rose-rose-1, rose-qdrant-1)
✅ Backend API: Healthy
✅ Groq Service: Connected
✅ ElevenLabs: Connected
✅ Qdrant: Connected
✅ SQLite: Connected
✅ Frontend: Serving
✅ Static Assets: Accessible
✅ Environment: Configured
⚠️ Memory: 345MB / 512MB (67% - Warning)
✅ Recent Errors: None

Overall Status: 🎉 ALL SYSTEMS GO
```

## Action Items

If any checks fail:
- Document the specific failure
- Check relevant logs
- Provide troubleshooting steps
- Suggest fixes
