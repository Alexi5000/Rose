# Monitoring Quick Start Guide

This guide provides a quick reference for setting up and using the Rose monitoring and alerting system.

## 5-Minute Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment Variables

Add to your `.env` file or Railway environment:

```bash
# Optional but recommended for production
SENTRY_DSN=https://your-key@sentry.io/project-id

# Alert thresholds (defaults shown)
ALERT_ERROR_RATE_THRESHOLD=5.0
ALERT_RESPONSE_TIME_THRESHOLD=2000.0
ALERT_MEMORY_THRESHOLD=80.0
```

### 3. Deploy

```bash
git add .
git commit -m "Enable monitoring"
git push
```

### 4. Verify

```bash
curl https://your-app.railway.app/api/v1/monitoring/status
```

## Quick Reference

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/monitoring/metrics` | GET | Current metrics |
| `/api/v1/monitoring/status` | GET | Monitoring status |
| `/api/v1/monitoring/alerts` | GET | Alert history |
| `/api/v1/monitoring/evaluate` | POST | Trigger evaluation |

### Default Alert Thresholds

| Alert | Metric | Threshold | Action |
|-------|--------|-----------|--------|
| High Error Rate | Error % | > 5% | Investigate errors |
| Slow Response | P95 time | > 2000ms | Check performance |
| High Memory | Memory % | > 80% | Check memory leaks |
| Circuit Breaker | Open count | > 0 | Check external APIs |

### Environment Variables

```bash
# Sentry (optional)
SENTRY_DSN=                          # Sentry project DSN
SENTRY_TRACES_SAMPLE_RATE=0.1       # 10% transaction sampling
ENVIRONMENT=production               # Environment name
APP_VERSION=1.0.0                    # Release version

# Alerts
ALERT_ERROR_RATE_ENABLED=true       # Enable error rate alerts
ALERT_ERROR_RATE_THRESHOLD=5.0      # Error rate % threshold
ALERT_RESPONSE_TIME_ENABLED=true    # Enable response time alerts
ALERT_RESPONSE_TIME_THRESHOLD=2000  # Response time ms threshold
ALERT_MEMORY_ENABLED=true           # Enable memory alerts
ALERT_MEMORY_THRESHOLD=80.0         # Memory % threshold
ALERT_CIRCUIT_BREAKER_ENABLED=true  # Enable circuit breaker alerts

# Scheduler
MONITORING_EVALUATION_INTERVAL=60   # Evaluation interval in seconds
```

## Common Tasks

### Check Current Metrics

```bash
curl https://your-app.railway.app/api/v1/monitoring/metrics | jq
```

### View Active Alerts

```bash
curl https://your-app.railway.app/api/v1/monitoring/status | jq '.active_alerts'
```

### View Last 24 Hours of Alerts

```bash
curl https://your-app.railway.app/api/v1/monitoring/alerts?hours=24 | jq
```

### Manually Trigger Alert Check

```bash
curl -X POST https://your-app.railway.app/api/v1/monitoring/evaluate | jq
```

## Sentry Setup (5 minutes)

### 1. Create Account

Go to https://sentry.io and sign up (free tier available)

### 2. Create Project

- Click "Create Project"
- Select "FastAPI" as platform
- Name it "rose-production"

### 3. Get DSN

- Go to Settings → Projects → rose-production → Client Keys (DSN)
- Copy the DSN URL

### 4. Add to Railway

In Railway dashboard:
- Go to your service
- Click "Variables"
- Add new variable:
  - Name: `SENTRY_DSN`
  - Value: `https://your-key@sentry.io/project-id`
- Click "Deploy"

### 5. Configure Alerts

In Sentry dashboard:
- Go to Alerts → Create Alert Rule
- Set conditions:
  - Error rate > 5% in 5 minutes
  - Response time P95 > 2 seconds
- Add notification channel (email, Slack)

## Troubleshooting

### Sentry Not Working

**Check**:
```bash
curl https://your-app.railway.app/api/v1/monitoring/status | jq '.sentry_enabled'
```

Should return `true`. If `false`:
1. Verify `SENTRY_DSN` is set in Railway
2. Check Railway logs for "sentry_initialized"
3. Verify no firewall blocking sentry.io

### No Alerts Triggering

**Check**:
```bash
curl -X POST https://your-app.railway.app/api/v1/monitoring/evaluate | jq
```

If no alerts triggered:
1. Verify thresholds are appropriate for your traffic
2. Check if alerts are enabled (`ALERT_*_ENABLED=true`)
3. Review metrics to see current values

### High Memory Alerts

**Actions**:
1. Check Railway dashboard for memory trends
2. Verify audio cleanup is running (check logs)
3. Check session cleanup is working
4. Consider increasing memory limits

## Monitoring Dashboard

### Railway Built-in Metrics

View in Railway dashboard:
- CPU usage
- Memory usage
- Network I/O
- Disk usage

### Custom Metrics

View via API:
```bash
curl https://your-app.railway.app/api/v1/monitoring/metrics | jq
```

### Sentry Dashboard

View at https://sentry.io:
- Error tracking
- Performance monitoring
- Release tracking
- Alert history

## Alert Response

### High Error Rate Alert

1. Check Sentry for error details
2. Review recent deployments
3. Check external API status (Groq, ElevenLabs, Qdrant)
4. Review logs for patterns
5. Consider rollback if needed

### Slow Response Time Alert

1. Check Railway metrics for resource usage
2. Review API call durations in metrics
3. Check external API latency
4. Look for database locks
5. Consider scaling resources

### High Memory Usage Alert

1. Check Railway memory graph
2. Review session count
3. Check audio file cleanup
4. Look for memory leaks in logs
5. Consider increasing memory limit

### Circuit Breaker Open Alert

1. Check which service has open circuit
2. Verify external API status
3. Review error logs for that service
4. Wait for circuit to close (60s default)
5. Check if issue persists

## Best Practices

### Development

```bash
# Disable alerts in development
ALERT_ERROR_RATE_ENABLED=false
ALERT_RESPONSE_TIME_ENABLED=false
MONITORING_EVALUATION_INTERVAL=300  # 5 minutes
```

### Staging

```bash
# Relaxed thresholds for staging
ALERT_ERROR_RATE_THRESHOLD=10.0
ALERT_RESPONSE_TIME_THRESHOLD=3000.0
MONITORING_EVALUATION_INTERVAL=120  # 2 minutes
```

### Production

```bash
# Strict thresholds for production
ALERT_ERROR_RATE_THRESHOLD=5.0
ALERT_RESPONSE_TIME_THRESHOLD=2000.0
MONITORING_EVALUATION_INTERVAL=60  # 1 minute
SENTRY_DSN=https://your-key@sentry.io/project-id
```

## Next Steps

1. ✅ Deploy monitoring system
2. ✅ Configure Sentry
3. ✅ Set up alert thresholds
4. ✅ Test alert notifications
5. ✅ Create monitoring dashboard bookmarks
6. ✅ Document alert response procedures
7. ✅ Train team on monitoring tools

## Resources

- **Full Documentation**: [MONITORING_AND_ALERTING.md](./MONITORING_AND_ALERTING.md)
- **Railway Setup**: [RAILWAY_SETUP.md](./RAILWAY_SETUP.md)
- **Operations Runbook**: [OPERATIONS_RUNBOOK.md](./OPERATIONS_RUNBOOK.md)
- **Sentry Docs**: https://docs.sentry.io
- **Railway Docs**: https://docs.railway.app

## Support

For help:
- Check logs: `railway logs` or Railway dashboard
- Review Sentry dashboard
- Check monitoring status endpoint
- Consult operations runbook
