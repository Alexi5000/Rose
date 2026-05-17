# Review Application Logs

Analyze recent application logs for errors, warnings, and performance insights.

## Log Review Commands

### 1. Recent Logs (Last 100 lines)
```bash
docker-compose logs rose --tail 100
```

### 2. Follow Logs in Real-Time
```bash
docker-compose logs -f rose
```

### 3. Errors Only
```bash
docker-compose logs rose --tail 500 | grep -E "(ERROR|❌|error|failed|Failed)"
```

### 4. Voice Processing Events
```bash
docker-compose logs rose --tail 500 | grep -E "(🎤|voice|🔊|audio|groq|elevenlabs)"
```

### 5. Performance Metrics
```bash
docker-compose logs rose --tail 500 | grep -E "(duration_ms|📊|metrics)"
```

### 6. Health Checks
```bash
docker-compose logs rose --tail 200 | grep -E "(health|🏥)"
```

### 7. Session Events
```bash
docker-compose logs rose --tail 500 | grep -E "(session_id|session_started|session_ended)"
```

### 8. API Requests
```bash
docker-compose logs rose --tail 500 | grep -E "(POST|GET|PUT|DELETE|📤|📥)"
```

## Log Analysis

### Count Events by Type

```bash
echo "📊 Log Event Summary"
echo "===================="

# Total log lines
echo "Total logs: $(docker-compose logs rose --tail 1000 | wc -l)"

# Errors
echo "Errors: $(docker-compose logs rose --tail 1000 | grep -c -E 'ERROR|❌')"

# Voice requests
echo "Voice requests: $(docker-compose logs rose --tail 1000 | grep -c '🎤 voice_processing_started')"

# Health checks
echo "Health checks: $(docker-compose logs rose --tail 1000 | grep -c 'health_check_complete')"

# Workflow executions
echo "Workflow runs: $(docker-compose logs rose --tail 1000 | grep -c 'workflow_execution_success')"

# API errors
echo "API errors: $(docker-compose logs rose --tail 1000 | grep -c 'api.*failed')"
```

### Recent Error Analysis

```bash
echo "🔍 Recent Errors (Last Hour)"
echo "============================"

docker-compose logs rose --since 1h | grep -E "ERROR|❌|error|failed" | tail -20

# If any errors found, provide context:
# - What endpoint/service?
# - What was the error message?
# - Any session_id or request_id for tracing?
```

### Performance Analysis

```bash
echo "⚡ Performance Metrics"
echo "===================="

# Average voice processing time
docker-compose logs rose --tail 500 | \
  grep "voice_processing_duration" | \
  awk '{print $NF}' | \
  awk '{ total += $1; count++ } END { print "Avg voice processing: " total/count " ms" }'

# Average workflow execution time
docker-compose logs rose --tail 500 | \
  grep "workflow_execution" | \
  grep "duration_ms" | \
  awk '{print $NF}' | \
  awk '{ total += $1; count++ } END { print "Avg workflow time: " total/count " ms" }'

# Health check response time
docker-compose logs rose --tail 500 | \
  grep "health_check_duration" | \
  awk '{print $NF}' | \
  awk '{ total += $1; count++ } END { print "Avg health check: " total/count " ms" }'
```

### Service Call Analysis

```bash
echo "🌐 External API Calls"
echo "===================="

# Groq STT calls
echo "Groq STT: $(docker-compose logs rose --tail 1000 | grep -c 'groq_stt')"

# Groq LLM calls
echo "Groq LLM: $(docker-compose logs rose --tail 1000 | grep -c 'groq.*llm')"

# ElevenLabs TTS calls
echo "ElevenLabs TTS: $(docker-compose logs rose --tail 1000 | grep -c 'elevenlabs_tts')"

# Qdrant operations
echo "Qdrant ops: $(docker-compose logs rose --tail 1000 | grep -c 'qdrant')"
```

## Log Pattern Detection

### Warning Signs to Look For

**Memory Issues:**
```bash
docker-compose logs rose --tail 1000 | grep -i "memory\|oom\|out of memory"
```

**Connection Issues:**
```bash
docker-compose logs rose --tail 1000 | grep -i "connection\|timeout\|refused"
```

**Rate Limiting:**
```bash
docker-compose logs rose --tail 1000 | grep -i "rate limit\|429\|too many requests"
```

**API Key Issues:**
```bash
docker-compose logs rose --tail 1000 | grep -i "unauthorized\|401\|api key\|authentication"
```

**Circuit Breaker:**
```bash
docker-compose logs rose --tail 1000 | grep -i "circuit.*open\|circuit breaker"
```

## Log Export

### Save Logs to File

```bash
# Export all logs
docker-compose logs rose > rose_logs_$(date +%Y%m%d_%H%M%S).log

# Export errors only
docker-compose logs rose --tail 1000 | grep -E "ERROR|❌" > rose_errors_$(date +%Y%m%d_%H%M%S).log

# Export with timestamps
docker-compose logs rose --timestamps --tail 1000 > rose_logs_timestamped.log
```

## Log Report Format

```markdown
# 📋 Log Analysis Report

**Time Range**: Last 1000 log lines
**Analysis Date**: [timestamp]

## Summary Statistics
- Total log entries: XXX
- Error count: XX
- Warning count: XX
- Voice requests: XX
- Health checks: XX

## Error Analysis
### Recent Errors (Last 10):
[List recent errors with context]

### Error Patterns:
- Connection timeouts: X occurrences
- API failures: X occurrences
- Validation errors: X occurrences

## Performance Metrics
- Avg voice processing: XX.XX ms
- Avg workflow execution: XX.XX ms
- Avg health check: XX.XX ms

## Service Health
- Groq API: XXX calls (X failures)
- ElevenLabs: XXX calls (X failures)
- Qdrant: XXX operations (X failures)

## Recommendations
[Based on log analysis, provide recommendations]

1. If errors > 10: Investigate error patterns
2. If avg processing > 15000ms: Check API latency
3. If connection errors: Verify network/API keys
4. If memory warnings: Check for memory leaks

## Action Items
- [ ] [Action item based on findings]
- [ ] [Action item based on findings]
```

## Quick Diagnostics

### Is Everything Working?
```bash
#!/bin/bash
echo "🔍 Quick Log Diagnostics"
echo "======================="

# Check for recent startup
if docker-compose logs rose --tail 50 | grep -q "Application startup complete"; then
  echo "✅ Server started successfully"
else
  echo "⚠️ No recent startup detected"
fi

# Check for recent health checks
if docker-compose logs rose --tail 50 | grep -q "health_check_complete"; then
  echo "✅ Health checks running"
else
  echo "⚠️ No recent health checks"
fi

# Check for errors in last 100 lines
error_count=$(docker-compose logs rose --tail 100 | grep -c -E "ERROR|❌")
if [ "$error_count" -eq 0 ]; then
  echo "✅ No recent errors"
else
  echo "❌ Found $error_count errors in last 100 lines"
fi

# Check for voice activity
if docker-compose logs rose --tail 100 | grep -q "voice_processing"; then
  echo "✅ Voice processing active"
else
  echo "ℹ️  No recent voice activity"
fi

echo ""
echo "Overall: $([ $error_count -eq 0 ] && echo '🎉 Looking good!' || echo '⚠️ Check errors above')"
```
