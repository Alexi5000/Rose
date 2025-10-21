# Operations Runbook: Rose the Healer Shaman

This runbook provides troubleshooting procedures, diagnostic steps, and solutions for common operational issues with the Rose application.

## Table of Contents

- [Quick Reference](#quick-reference)
- [Common Issues](#common-issues)
  - [High Error Rate](#high-error-rate)
  - [Slow Response Times](#slow-response-times)
  - [Memory Issues](#memory-issues)
  - [Database Issues](#database-issues)
  - [External API Failures](#external-api-failures)
  - [Audio Processing Failures](#audio-processing-failures)
- [Diagnostic Procedures](#diagnostic-procedures)
- [Emergency Procedures](#emergency-procedures)
- [Monitoring and Alerts](#monitoring-and-alerts)

---

## Quick Reference

### Key Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `/api/health` | Health check | `{"status": "healthy", ...}` |
| `/api/session/start` | Start new session | `{"session_id": "..."}` |
| `/api/voice/process` | Process voice input | `{"text": "...", "audio_url": "..."}` |

### Key Metrics to Monitor

- **Error Rate**: Should be < 1% under normal conditions
- **Response Time**: P95 should be < 5 seconds for voice processing
- **Memory Usage**: Should stay under 80% of allocated memory
- **Disk Usage**: `/app/data` should not exceed 80% capacity
- **Active Sessions**: Track concurrent session count

### Log Locations

- **Application Logs**: stdout/stderr (captured by platform)
- **Structured Logs**: JSON format with request IDs
- **Backup Logs**: `/app/data/backups/backup.log`

### External Service Status Pages

- **Groq**: https://status.groq.com/
- **ElevenLabs**: https://status.elevenlabs.io/
- **Qdrant Cloud**: https://status.qdrant.io/
- **Railway**: https://railway.app/status

---

## Common Issues

### High Error Rate

#### Symptoms
- Error rate > 5% in monitoring dashboard
- Multiple 500 errors in logs
- Users reporting failures

#### Diagnostic Steps

1. **Check Application Logs**
   ```bash
   # Railway
   railway logs --tail 100
   
   # Check for error patterns
   railway logs | grep "ERROR"
   ```

2. **Verify External Service Status**
   - Check Groq status page
   - Check ElevenLabs status page
   - Check Qdrant status page

3. **Check Circuit Breaker Status**
   - Look for "Circuit breaker OPEN" messages in logs
   - Indicates repeated failures to external service

4. **Review Recent Deployments**
   - Check if error rate increased after deployment
   - Consider rollback if correlation exists

#### Common Causes and Solutions

**Cause: External API Outage**
- **Solution**: Circuit breakers should handle this automatically
- **Action**: Monitor external service status pages
- **Recovery**: Errors should resolve when service recovers

**Cause: Invalid API Keys**
- **Solution**: Verify environment variables
  ```bash
  railway variables
  ```
- **Action**: Check for expired or revoked keys
- **Recovery**: Update keys and redeploy

**Cause: Rate Limit Exceeded**
- **Solution**: Check API usage against quotas
- **Action**: Implement request queuing or upgrade API plan
- **Recovery**: Wait for rate limit reset or upgrade plan

**Cause: Memory Exhaustion**
- **Solution**: Check memory usage metrics
- **Action**: Restart service or increase memory allocation
- **Recovery**: See [Memory Issues](#memory-issues) section

---

### Slow Response Times

#### Symptoms
- Response times > 10 seconds
- Users reporting delays
- Timeout errors in logs

#### Diagnostic Steps

1. **Check Performance Metrics**
   ```bash
   # Look for timing logs
   railway logs | grep "duration_ms"
   ```

2. **Identify Bottleneck**
   - Check Groq API latency (look for "groq_duration_ms")
   - Check Qdrant query times (look for "qdrant_duration_ms")
   - Check TTS generation times (look for "tts_duration_ms")

3. **Check Concurrent Load**
   - Review active session count
   - Check if slowdown correlates with high traffic

4. **Verify Network Connectivity**
   - Test external API connectivity from deployment region
   - Check for network issues between services

#### Common Causes and Solutions

**Cause: Groq API Slow**
- **Solution**: Groq may be experiencing high load
- **Action**: Monitor Groq status page
- **Temporary Fix**: Consider switching to faster model (gemma2-9b)
- **Recovery**: Performance should improve when Groq load decreases

**Cause: Qdrant Query Slow**
- **Solution**: Large vector database or complex queries
- **Action**: Check Qdrant collection size
- **Optimization**: Reduce `MEMORY_TOP_K` setting (default: 3)
- **Recovery**: Consider upgrading Qdrant plan

**Cause: High Concurrent Sessions**
- **Solution**: Application under heavy load
- **Action**: Check active session count in logs
- **Scaling**: Increase instance size or add horizontal scaling
- **Recovery**: Scale resources or implement request queuing

**Cause: Memory Pressure**
- **Solution**: Application swapping or near memory limit
- **Action**: Check memory usage metrics
- **Recovery**: Restart service or increase memory allocation

---

### Memory Issues

#### Symptoms
- Out of memory (OOM) errors
- Application crashes
- Slow performance with high memory usage
- Platform warnings about memory limits

#### Diagnostic Steps

1. **Check Memory Usage**
   ```bash
   # Railway dashboard shows memory metrics
   # Look for memory usage trends
   ```

2. **Check for Memory Leaks**
   - Review memory usage over time
   - Look for steady increase without corresponding load

3. **Check Session Count**
   ```bash
   # Count active sessions in database
   railway logs | grep "active_sessions"
   ```

4. **Check Temporary Files**
   ```bash
   # SSH into container (if available) or check logs
   railway logs | grep "audio_cleanup"
   ```

#### Common Causes and Solutions

**Cause: Too Many Active Sessions**
- **Solution**: Old sessions not being cleaned up
- **Action**: Check session cleanup job is running
  ```bash
  railway logs | grep "session_cleanup"
  ```
- **Fix**: Manually trigger cleanup or reduce retention period
- **Prevention**: Ensure cleanup job runs daily

**Cause: Temporary Audio Files Not Cleaned**
- **Solution**: Audio cleanup job not running
- **Action**: Check for cleanup logs
  ```bash
  railway logs | grep "cleanup_old_audio"
  ```
- **Fix**: Restart service to reinitialize cleanup job
- **Prevention**: Monitor disk usage regularly

**Cause: Large Vector Database**
- **Solution**: Qdrant memory usage growing
- **Action**: Check Qdrant collection size
- **Optimization**: Implement memory pruning or archival
- **Recovery**: Consider upgrading Qdrant plan

**Cause: Memory Leak**
- **Solution**: Application not releasing memory
- **Action**: Review recent code changes
- **Temporary Fix**: Restart service
- **Long-term**: Profile application and fix leak

---

### Database Issues

#### Symptoms
- "Database locked" errors
- Slow query performance
- Data corruption warnings
- Session state not persisting

#### Diagnostic Steps

1. **Check Database Health**
   ```bash
   # Health endpoint includes database check
   curl https://your-app.railway.app/api/health
   ```

2. **Check Database Size**
   ```bash
   railway logs | grep "database_size"
   ```

3. **Check for Corruption**
   ```bash
   railway logs | grep "database" | grep -i "corrupt\|error"
   ```

4. **Verify Volume Mount**
   - Check Railway dashboard for volume configuration
   - Ensure `/app/data` is mounted to persistent volume

#### Common Causes and Solutions

**Cause: Database Locked (SQLite)**
- **Solution**: Concurrent write attempts
- **Action**: Check for multiple processes accessing database
- **Temporary Fix**: Restart service
- **Long-term**: Consider PostgreSQL for better concurrency

**Cause: Database Corruption**
- **Solution**: Unexpected shutdown or disk issues
- **Action**: Check backup availability
  ```bash
  railway logs | grep "backup_created"
  ```
- **Recovery**: Restore from most recent backup
- **Prevention**: Ensure proper shutdown procedures

**Cause: Volume Not Mounted**
- **Solution**: Data stored on ephemeral storage
- **Action**: Check Railway volume configuration
- **Fix**: Add persistent volume and redeploy
- **Impact**: Previous data may be lost

**Cause: Disk Full**
- **Solution**: Volume capacity exceeded
- **Action**: Check disk usage
- **Fix**: Increase volume size or clean old data
- **Prevention**: Monitor disk usage regularly

---

### External API Failures

#### Symptoms
- "Service unavailable" errors
- Circuit breaker open messages
- Specific API error messages (Groq, ElevenLabs, Qdrant)

#### Diagnostic Steps

1. **Identify Failing Service**
   ```bash
   railway logs | grep -i "groq\|elevenlabs\|qdrant" | grep -i "error\|fail"
   ```

2. **Check Circuit Breaker Status**
   ```bash
   railway logs | grep "circuit_breaker"
   ```

3. **Verify API Keys**
   ```bash
   railway variables | grep -i "api_key"
   ```

4. **Test API Connectivity**
   - Use health endpoint to test all services
   - Check service status pages

#### Common Causes and Solutions

**Cause: Groq API Down**
- **Symptoms**: STT or LLM failures
- **Solution**: Circuit breaker prevents cascading failures
- **Action**: Monitor Groq status page
- **User Impact**: Graceful error messages shown
- **Recovery**: Automatic when Groq recovers

**Cause: ElevenLabs API Down**
- **Symptoms**: TTS failures, no audio responses
- **Solution**: Fallback to text-only responses
- **Action**: Monitor ElevenLabs status page
- **User Impact**: Text responses still work
- **Recovery**: Automatic when ElevenLabs recovers

**Cause: Qdrant Connection Issues**
- **Symptoms**: Memory retrieval failures
- **Solution**: Application continues with degraded memory
- **Action**: Check Qdrant URL and API key
- **User Impact**: Reduced context awareness
- **Recovery**: Verify credentials and connectivity

**Cause: Rate Limit Exceeded**
- **Symptoms**: 429 errors in logs
- **Solution**: Retry logic with backoff
- **Action**: Check API usage against quotas
- **Mitigation**: Implement request queuing
- **Long-term**: Upgrade API plan

---

### Audio Processing Failures

#### Symptoms
- "Audio processing failed" errors
- Invalid audio format errors
- Corrupted audio file warnings

#### Diagnostic Steps

1. **Check Audio Validation Logs**
   ```bash
   railway logs | grep "audio_validation"
   ```

2. **Check File Size Limits**
   ```bash
   railway logs | grep "audio_size"
   ```

3. **Check Temporary Storage**
   ```bash
   railway logs | grep "tmp" | grep -i "error"
   ```

4. **Verify Audio Format**
   - Check client is sending supported formats
   - Review audio encoding settings

#### Common Causes and Solutions

**Cause: Invalid Audio Format**
- **Symptoms**: Format validation errors
- **Solution**: Client sending unsupported format
- **Action**: Check frontend audio recording settings
- **Fix**: Ensure WebM or WAV format
- **Prevention**: Add format validation in frontend

**Cause: Audio File Too Large**
- **Symptoms**: Size limit exceeded errors
- **Solution**: Audio exceeds 10MB limit
- **Action**: Check recording duration
- **Fix**: Implement client-side duration limits
- **Prevention**: Add UI feedback for recording length

**Cause: Corrupted Audio Data**
- **Symptoms**: Decoding errors
- **Solution**: Network issues during upload
- **Action**: Check network stability
- **Fix**: Implement retry logic in frontend
- **Prevention**: Add audio integrity checks

**Cause: Temporary Storage Full**
- **Symptoms**: Cannot write audio file
- **Solution**: Disk space exhausted
- **Action**: Check disk usage
- **Fix**: Trigger manual cleanup or increase storage
- **Prevention**: Ensure cleanup job runs regularly

---

## Diagnostic Procedures

### Health Check Procedure

1. **Basic Health Check**
   ```bash
   curl https://your-app.railway.app/api/health
   ```
   
   Expected response:
   ```json
   {
     "status": "healthy",
     "timestamp": "2024-01-15T10:30:00Z",
     "services": {
       "groq": "healthy",
       "elevenlabs": "healthy",
       "qdrant": "healthy",
       "database": "healthy"
     }
   }
   ```

2. **Detailed Service Check**
   - If any service shows "unhealthy", investigate that service
   - Check service-specific logs
   - Verify credentials and connectivity

### Log Analysis Procedure

1. **Get Recent Logs**
   ```bash
   railway logs --tail 500 > logs.txt
   ```

2. **Search for Errors**
   ```bash
   grep "ERROR" logs.txt
   grep "CRITICAL" logs.txt
   grep "exception" logs.txt -i
   ```

3. **Identify Patterns**
   - Look for repeated errors
   - Check timestamps for correlation
   - Identify affected endpoints or sessions

4. **Extract Request IDs**
   ```bash
   grep "request_id" logs.txt | grep "ERROR"
   ```
   - Use request IDs to trace full request lifecycle

### Performance Analysis Procedure

1. **Extract Timing Metrics**
   ```bash
   railway logs | grep "duration_ms" > timings.txt
   ```

2. **Calculate Percentiles**
   - Identify P50, P95, P99 response times
   - Compare against SLA targets

3. **Identify Slow Operations**
   - Find operations > 5 seconds
   - Determine which service is slow

4. **Check Resource Usage**
   - Review memory usage trends
   - Check CPU utilization
   - Monitor disk I/O

---

## Emergency Procedures

### Service Down - Complete Outage

**Immediate Actions:**

1. **Check Service Status**
   ```bash
   railway status
   ```

2. **Check Recent Deployments**
   - Review deployment history
   - Identify if outage started after deployment

3. **Attempt Service Restart**
   ```bash
   railway restart
   ```

4. **Check Logs for Crash Cause**
   ```bash
   railway logs --tail 200
   ```

5. **If Restart Fails, Rollback**
   - See [Rollback Procedures](ROLLBACK_PROCEDURES.md)

**Communication:**
- Update status page (if available)
- Notify users via appropriate channels
- Provide ETA for resolution

### Data Loss Event

**Immediate Actions:**

1. **Stop Service**
   ```bash
   railway down
   ```

2. **Assess Damage**
   - Check what data is affected
   - Verify backup availability

3. **Restore from Backup**
   - See [Rollback Procedures](ROLLBACK_PROCEDURES.md)
   - Follow backup restoration steps

4. **Verify Data Integrity**
   - Test restored data
   - Verify session continuity

5. **Resume Service**
   ```bash
   railway up
   ```

**Post-Incident:**
- Document what happened
- Identify root cause
- Implement preventive measures

### Security Incident

**Immediate Actions:**

1. **Isolate Affected Systems**
   - Take service offline if necessary
   - Block suspicious IP addresses

2. **Rotate All Credentials**
   ```bash
   railway variables set GROQ_API_KEY=new_key
   railway variables set ELEVENLABS_API_KEY=new_key
   # Rotate all API keys
   ```

3. **Review Access Logs**
   - Identify unauthorized access
   - Determine scope of breach

4. **Notify Stakeholders**
   - Follow incident response plan
   - Comply with disclosure requirements

5. **Restore Service Securely**
   - Verify all credentials rotated
   - Implement additional security measures

---

## Monitoring and Alerts

### Recommended Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Error Rate | > 2% | > 5% | Investigate logs, check external services |
| Response Time (P95) | > 8s | > 15s | Check performance metrics, scale if needed |
| Memory Usage | > 70% | > 85% | Check for leaks, restart if needed |
| Disk Usage | > 70% | > 85% | Clean old data, increase volume size |
| Circuit Breaker Open | Any | Multiple | Check external service status |
| Health Check Failures | 2 consecutive | 5 consecutive | Restart service, investigate |

### Monitoring Setup

**Railway Built-in Metrics:**
- CPU usage
- Memory usage
- Network traffic
- Request count

**Application Metrics (via Logs):**
- Error rate by endpoint
- Response time percentiles
- Active session count
- Circuit breaker status
- Backup success/failure

**External Monitoring:**
- Uptime monitoring (UptimeRobot, Pingdom)
- Error tracking (Sentry)
- Log aggregation (Logtail, Papertrail)

### Log Monitoring Queries

**High Error Rate:**
```bash
railway logs | grep "ERROR" | wc -l
```

**Slow Requests:**
```bash
railway logs | grep "duration_ms" | awk -F'"duration_ms":' '{print $2}' | awk -F',' '{print $1}' | sort -n | tail -20
```

**Circuit Breaker Events:**
```bash
railway logs | grep "circuit_breaker" | grep "OPEN"
```

**Active Sessions:**
```bash
railway logs | grep "active_sessions" | tail -1
```

---

## Escalation Procedures

### Level 1: On-Call Engineer
- Initial response to alerts
- Basic troubleshooting
- Service restarts
- Log analysis

### Level 2: Senior Engineer
- Complex troubleshooting
- Performance optimization
- Database issues
- Code-level debugging

### Level 3: Engineering Lead
- Architecture decisions
- Major incidents
- Data loss events
- Security incidents

### External Escalation
- **Groq Support**: support@groq.com
- **ElevenLabs Support**: support@elevenlabs.io
- **Qdrant Support**: support@qdrant.io
- **Railway Support**: help@railway.app

---

## Related Documentation

- [Rollback Procedures](ROLLBACK_PROCEDURES.md)
- [Incident Response Plan](INCIDENT_RESPONSE_PLAN.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Data Persistence Guide](DATA_PERSISTENCE.md)
- [Monitoring and Observability](MONITORING_AND_OBSERVABILITY.md)

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2024-01-15 | 1.0 | Initial runbook creation |
