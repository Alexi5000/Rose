# Operations Runbook

## Overview

This runbook provides troubleshooting guidance for common operational issues with the Rose the Healer Shaman application. Use this guide for quick diagnosis and resolution of production incidents.

## Quick Reference

| Issue | Severity | First Response |
|-------|----------|----------------|
| High error rate | Critical | Check external API status, review logs |
| Slow response times | High | Check Qdrant connectivity, memory usage |
| Memory issues | High | Check database size, temporary files |
| Audio processing failures | Medium | Verify Groq/ElevenLabs API keys |
| Session not found | Low | Check SQLite database, session cleanup |

## Common Issues

### 1. High Error Rate

**Symptoms:**
- Multiple 500 errors in logs
- Users reporting failed requests
- Error rate > 5% in monitoring dashboard

**Diagnosis:**
```bash
# Check recent error logs
grep "ERROR" /app/logs/app.log | tail -50

# Check external API status
curl https://api.groq.com/health
curl https://api.elevenlabs.io/health

# Verify environment variables
env | grep -E "(GROQ|ELEVENLABS|QDRANT)"
```

**Resolution:**
1. **External API Issues:**
   - Check status pages: Groq, ElevenLabs, Qdrant
   - Verify API keys are valid and not expired
   - Check rate limits haven't been exceeded
   - Wait for service recovery or switch to backup provider

2. **Configuration Issues:**
   - Verify all required environment variables are set
   - Check CORS configuration matches frontend origin
   - Restart service to reload configuration

3. **Database Issues:**
   - Check SQLite database file permissions
   - Verify Qdrant connection with health check endpoint
   - Check disk space availability

**Prevention:**
- Implement circuit breakers for external services
- Set up monitoring alerts for error rate > 3%
- Regular API key rotation schedule

---

### 2. Slow Response Times

**Symptoms:**
- Response times > 5 seconds
- Users reporting lag or timeouts
- High CPU or memory usage

**Diagnosis:**
```bash
# Check system resources
docker stats

# Check database size
ls -lh /app/data/*.db

# Check temporary file count
find /tmp -name "*.wav" -o -name "*.mp3" | wc -l

# Check active sessions
sqlite3 /app/data/short_term_memory.db "SELECT COUNT(*) FROM sessions;"
```

**Resolution:**
1. **High Memory Usage:**
   - Restart service to clear memory leaks
   - Check for large audio files in /tmp
   - Run cleanup job: `python -m ai_companion.core.session_cleanup`

2. **Database Performance:**
   - Check SQLite database size (should be < 100MB)
   - Run VACUUM on SQLite: `sqlite3 /app/data/short_term_memory.db "VACUUM;"`
   - Archive old sessions (> 7 days)

3. **External API Latency:**
   - Check Qdrant response times
   - Verify network connectivity to external services
   - Consider enabling TTS caching

4. **High Concurrent Load:**
   - Check number of active sessions
   - Consider scaling horizontally (requires PostgreSQL migration)
   - Implement request queuing

**Prevention:**
- Set up monitoring for response time > 3s
- Implement automatic session cleanup
- Configure memory limits in Docker

---

### 3. Memory Issues / OOM Kills

**Symptoms:**
- Container restarts unexpectedly
- "Out of memory" errors in logs
- Railway shows memory limit exceeded

**Diagnosis:**
```bash
# Check memory usage
docker stats --no-stream

# Check for memory leaks
ps aux | grep python | awk '{print $6}'

# Check temporary files
du -sh /tmp

# Check database sizes
du -sh /app/data/
```

**Resolution:**
1. **Immediate:**
   - Restart service to clear memory
   - Clean up temporary files: `find /tmp -name "*.wav" -mtime +1 -delete`
   - Clear old sessions

2. **Short-term:**
   - Reduce concurrent session limit
   - Enable aggressive session cleanup
   - Increase memory limit in Railway

3. **Long-term:**
   - Implement automatic temporary file cleanup
   - Add memory profiling to identify leaks
   - Optimize Qdrant client connection pooling

**Prevention:**
- Configure Docker memory limits (512MB-1GB)
- Implement scheduled cleanup jobs
- Monitor memory usage trends

---

### 4. Audio Processing Failures

**Symptoms:**
- "Speech-to-text failed" errors
- "Text-to-speech failed" errors
- Users can't hear responses

**Diagnosis:**
```bash
# Check API keys
echo $GROQ_API_KEY | cut -c1-10
echo $ELEVENLABS_API_KEY | cut -c1-10

# Test Groq STT
curl -X POST https://api.groq.com/openai/v1/audio/transcriptions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -F file=@test.wav -F model=whisper-large-v3

# Test ElevenLabs TTS
curl -X POST https://api.elevenlabs.io/v1/text-to-speech/$ELEVENLABS_VOICE_ID \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text":"test"}'
```

**Resolution:**
1. **API Key Issues:**
   - Verify API keys are correct and active
   - Check API quota/credits remaining
   - Rotate keys if compromised

2. **Audio Format Issues:**
   - Verify audio file format (should be WAV/MP3)
   - Check file size (< 25MB for Groq)
   - Validate audio encoding

3. **Rate Limiting:**
   - Check if rate limits exceeded
   - Implement exponential backoff
   - Consider upgrading API plan

**Prevention:**
- Monitor API usage and quotas
- Implement circuit breakers
- Set up alerts for API failures > 10%

---

### 5. Qdrant Connection Issues

**Symptoms:**
- "Failed to connect to Qdrant" errors
- Memory retrieval failures
- Slow memory operations

**Diagnosis:**
```bash
# Test Qdrant connectivity
curl -X GET "$QDRANT_URL/health" \
  -H "api-key: $QDRANT_API_KEY"

# Check collection status
curl -X GET "$QDRANT_URL/collections/rose_memories" \
  -H "api-key: $QDRANT_API_KEY"

# Check network connectivity
ping $(echo $QDRANT_URL | sed 's|https://||' | sed 's|/.*||')
```

**Resolution:**
1. **Connection Failures:**
   - Verify QDRANT_URL and QDRANT_API_KEY
   - Check network connectivity
   - Verify Qdrant Cloud service status

2. **Collection Issues:**
   - Recreate collection if corrupted
   - Check collection size and limits
   - Verify vector dimensions match

3. **Performance Issues:**
   - Implement connection pooling
   - Add retry logic with backoff
   - Consider Qdrant plan upgrade

**Prevention:**
- Implement circuit breaker for Qdrant
- Monitor Qdrant response times
- Regular health checks

---

### 6. Session Not Found Errors

**Symptoms:**
- "Session not found" errors
- Users lose conversation context
- Inconsistent session state

**Diagnosis:**
```bash
# Check session in database
sqlite3 /app/data/short_term_memory.db \
  "SELECT * FROM checkpoints WHERE thread_id='<session_id>' LIMIT 1;"

# Check session count
sqlite3 /app/data/short_term_memory.db \
  "SELECT COUNT(DISTINCT thread_id) FROM checkpoints;"

# Check for cleanup job logs
grep "session_cleanup" /app/logs/app.log
```

**Resolution:**
1. **Session Expired:**
   - Normal behavior for sessions > 7 days
   - User needs to start new session
   - Frontend should handle gracefully

2. **Database Corruption:**
   - Restore from backup
   - Recreate database if necessary
   - Check disk space and permissions

3. **Cleanup Job Too Aggressive:**
   - Adjust cleanup threshold (default 7 days)
   - Disable automatic cleanup temporarily
   - Review cleanup logs

**Prevention:**
- Implement session persistence in frontend
- Regular database backups
- Monitor session lifecycle

---

### 7. Deployment Failures

**Symptoms:**
- Build fails on Railway
- Health checks fail after deployment
- Service won't start

**Diagnosis:**
```bash
# Check build logs in Railway dashboard
# Check startup logs
docker logs <container_id>

# Verify health check
curl http://localhost:8000/api/health

# Check environment variables
env | grep -E "(GROQ|ELEVENLABS|QDRANT|WHATSAPP)"
```

**Resolution:**
1. **Build Failures:**
   - Check pyproject.toml for dependency conflicts
   - Verify Python version (3.12+)
   - Check Docker build logs for errors

2. **Health Check Failures:**
   - Verify all external services are accessible
   - Check API keys are set correctly
   - Increase health check timeout

3. **Startup Failures:**
   - Check for missing environment variables
   - Verify database file permissions
   - Check port conflicts

**Prevention:**
- Run smoke tests before deployment
- Use CI/CD pipeline for validation
- Maintain deployment checklist

---

## Health Check Interpretation

### `/api/health` Endpoint Response

**Healthy Response (200 OK):**
```json
{
  "status": "healthy",
  "services": {
    "groq": "connected",
    "elevenlabs": "connected",
    "qdrant": "connected"
  },
  "timestamp": "2025-10-21T12:00:00Z"
}
```

**Degraded Response (503 Service Unavailable):**
```json
{
  "status": "degraded",
  "services": {
    "groq": "connected",
    "elevenlabs": "error",
    "qdrant": "connected"
  },
  "errors": ["ElevenLabs API unreachable"],
  "timestamp": "2025-10-21T12:00:00Z"
}
```

**Actions by Status:**
- `healthy`: No action needed
- `degraded`: Investigate failing service, may continue with reduced functionality
- `unhealthy`: Service should not receive traffic, investigate immediately

---

## Monitoring and Alerts

### Key Metrics to Monitor

1. **Error Rate**
   - Target: < 1%
   - Warning: > 3%
   - Critical: > 5%

2. **Response Time (p95)**
   - Target: < 2s
   - Warning: > 3s
   - Critical: > 5s

3. **Memory Usage**
   - Target: < 70%
   - Warning: > 80%
   - Critical: > 90%

4. **Active Sessions**
   - Target: < 100
   - Warning: > 150
   - Critical: > 200

5. **External API Errors**
   - Target: < 1%
   - Warning: > 5%
   - Critical: > 10%

### Alert Response Times

- **Critical**: Respond within 15 minutes
- **High**: Respond within 1 hour
- **Medium**: Respond within 4 hours
- **Low**: Respond within 24 hours

---

## Maintenance Tasks

### Daily
- Review error logs for patterns
- Check memory and disk usage
- Verify external API status

### Weekly
- Review performance metrics
- Check database sizes
- Clean up old temporary files
- Review session counts

### Monthly
- Rotate API keys
- Review and update dependencies
- Backup databases
- Review and update documentation

---

## Useful Commands

### Log Analysis
```bash
# View recent errors
grep "ERROR" /app/logs/app.log | tail -100

# Count errors by type
grep "ERROR" /app/logs/app.log | awk '{print $5}' | sort | uniq -c

# View slow requests (> 3s)
grep "duration" /app/logs/app.log | awk '$NF > 3000'
```

### Database Operations
```bash
# Database size
ls -lh /app/data/*.db

# Session count
sqlite3 /app/data/short_term_memory.db \
  "SELECT COUNT(DISTINCT thread_id) FROM checkpoints;"

# Old sessions (> 7 days)
sqlite3 /app/data/short_term_memory.db \
  "SELECT COUNT(*) FROM checkpoints WHERE created_at < datetime('now', '-7 days');"

# Vacuum database
sqlite3 /app/data/short_term_memory.db "VACUUM;"
```

### Cleanup Operations
```bash
# Clean old audio files
find /tmp -name "*.wav" -mtime +1 -delete
find /tmp -name "*.mp3" -mtime +1 -delete

# Clean old sessions
python -m ai_companion.core.session_cleanup --days 7

# Clear cache
rm -rf /app/cache/*
```

---

## Contact and Escalation

### On-Call Rotation
- Primary: [On-call engineer]
- Secondary: [Backup engineer]
- Manager: [Engineering manager]

### External Support
- **Groq**: support@groq.com
- **ElevenLabs**: support@elevenlabs.io
- **Qdrant**: support@qdrant.tech
- **Railway**: support@railway.app

### Escalation Path
1. On-call engineer (0-15 min)
2. Secondary engineer (15-30 min)
3. Engineering manager (30-60 min)
4. CTO (> 60 min for critical issues)

---

## Additional Resources

- [Deployment Guide](DEPLOYMENT.md)
- [Rollback Procedures](ROLLBACK_PROCEDURES.md)
- [Incident Response Plan](INCIDENT_RESPONSE_PLAN.md)
- [Architecture Documentation](ARCHITECTURE.md)
- [External API Limits](EXTERNAL_API_LIMITS.md)
