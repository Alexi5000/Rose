<!-- Rose full repository refresh 2026-05-17 -->
# Test Voice Interaction End-to-End

Run comprehensive voice interaction testing to verify the entire flow from recording to response playback.

## Steps to Execute

1. **Check Backend Health**
   - Verify backend is running: `docker-compose ps`
   - Check health endpoint: `curl http://localhost:8000/api/v1/health`
   - Verify all services connected (Groq, ElevenLabs, Qdrant, SQLite)

2. **Create Test Session**
   - Call session start: `curl -X POST http://localhost:8000/api/v1/session/start`
   - Save session_id for testing

3. **Review Recent Logs**
   - Check for any errors: `docker-compose logs rose --tail 100 | grep -E "(ERROR|❌|error)"`
   - Verify services are healthy

4. **Test Frontend Access**
   - Verify frontend loads: `curl -I http://localhost:8000/`
   - Check static assets: `curl -I http://localhost:8000/assets/index-*.js`

5. **Provide Testing Instructions**
   - Display step-by-step user testing guide
   - Explain "press and hold" pattern
   - List expected visual feedback

6. **Monitor for Issues**
   - Watch logs during test: `docker-compose logs -f rose`
   - Look for voice processing events (🎤, ✅, ❌)

## Expected Console Output

When testing in browser, expect to see:
```
🔌 Initializing API client with base URL: /api/v1
🎤 Processing voice input...
📤 API Request: POST /voice/process
✅ API Response: /voice/process Status: 200
✅ Voice processing successful
🔊 Playing audio response...
✅ Audio playback started
✅ Audio playback completed
```

## Success Criteria

✅ Backend health check returns {"status": "healthy"}
✅ Session creation returns valid session_id
✅ Frontend HTML loads successfully
✅ Static assets (CSS, JS) are accessible
✅ No errors in recent logs
✅ Clear testing instructions provided to user

## Troubleshooting

If issues found:
- Microphone permission: Check browser permissions
- API errors: Review backend logs for details
- Audio playback: Check browser console for errors
- Network issues: Verify Docker containers running
