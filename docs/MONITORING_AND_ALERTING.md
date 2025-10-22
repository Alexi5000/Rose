# Monitoring and Alerting System

This document describes the comprehensive monitoring and alerting system implemented for Rose the Healer Shaman application.

## Overview

The monitoring and alerting system provides:
- **Real-time metrics collection** - Track application performance and behavior
- **Automated alert evaluation** - Detect issues before they impact users
- **Error tracking integration** - Capture and track errors with Sentry
- **Monitoring dashboard** - View metrics and alerts via API endpoints
- **Configurable thresholds** - Customize alert sensitivity for your environment

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  - API Endpoints                                             │
│  - Background Jobs                                           │
│  - LangGraph Workflow                                        │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┬──────────────┬────────────────┐
        │                     │              │                │
┌───────▼────────┐  ┌────────▼─────┐  ┌────▼──────┐  ┌──────▼──────┐
│ Metrics        │  │ Monitoring   │  │ Alerting  │  │ Sentry      │
│ Collector      │  │ Scheduler    │  │ System    │  │ Integration │
│                │  │              │  │           │  │             │
│ - Counters     │  │ - Periodic   │  │ - Thresh- │  │ - Error     │
│ - Gauges       │  │   evaluation │  │   olds    │  │   tracking  │
│ - Histograms   │  │ - 60s        │  │ - Alerts  │  │ - Release   │
│                │  │   interval   │  │ - History │  │   tracking  │
└────────────────┘  └──────────────┘  └───────────┘  └─────────────┘
        │                     │              │                │
        └─────────────────────┴──────────────┴────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Structured Logs   │
                    │  (JSON format)     │
                    └────────────────────┘
```

## Components

### 1. Metrics Collector

Located in `src/ai_companion/core/metrics.py`, the metrics collector tracks:

**Counters:**
- `sessions_started` - Total sessions initiated
- `voice_requests_total` - Total voice processing requests
- `api_calls_{service}_{status}` - External API call counts by service and status
- `errors_total` - Total errors by type and endpoint
- `workflow_executions_{status}` - Workflow execution counts

**Histograms:**
- `voice_audio_size_bytes` - Audio file sizes
- `api_duration_ms_{service}` - API call durations by service
- `workflow_duration_ms` - Workflow execution times
- `{endpoint}_duration_ms` - Endpoint response times

**Usage Example:**
```python
from ai_companion.core.metrics import metrics

# Record a session start
metrics.record_session_started(session_id="abc123")

# Record an API call
metrics.record_api_call(
    service="groq",
    success=True,
    duration_ms=250.5
)

# Record an error
metrics.record_error(
    error_type="ValidationError",
    endpoint="/api/v1/voice/process"
)
```

### 2. Monitoring System

Located in `src/ai_companion/core/monitoring.py`, the monitoring system:

**Features:**
- Evaluates metrics against configurable thresholds
- Triggers alerts when thresholds are exceeded
- Integrates with Sentry for error tracking
- Maintains alert history
- Provides monitoring status API

**Alert Thresholds:**

| Alert Name | Metric | Default Threshold | Comparison |
|------------|--------|-------------------|------------|
| `high_error_rate` | Error rate percentage | 5.0% | Greater than |
| `slow_response_time` | P95 response time | 2000ms | Greater than |
| `high_memory_usage` | Memory usage | 80% | Greater than |
| `circuit_breaker_open` | Open circuit breakers | 0 | Greater than |

**Usage Example:**
```python
from ai_companion.core.monitoring import monitoring

# Manually evaluate thresholds
triggered_alerts = monitoring.evaluate_thresholds()

# Get active alerts
active_alerts = monitoring.get_active_alerts()

# Capture an exception
try:
    risky_operation()
except Exception as e:
    monitoring.capture_exception(e, context={"user_id": "123"})
```

### 3. Monitoring Scheduler

Located in `src/ai_companion/core/monitoring_scheduler.py`, the scheduler:
- Runs in the background as an async task
- Evaluates alert thresholds every 60 seconds (configurable)
- Automatically starts/stops with the application
- Logs evaluation results

### 4. Sentry Integration

Sentry provides:
- **Error tracking** - Automatic capture of exceptions
- **Performance monitoring** - Transaction tracing
- **Release tracking** - Track deployments and versions
- **Breadcrumbs** - Context leading up to errors
- **User feedback** - Optional user feedback collection

## Configuration

### Environment Variables

Add these to your `.env` file or Railway environment variables:

```bash
# Sentry Configuration (optional but recommended)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions
SENTRY_PROFILES_SAMPLE_RATE=0.1  # 10% of transactions
ENVIRONMENT=production
APP_VERSION=1.0.0

# Alert Configuration
ALERT_ERROR_RATE_ENABLED=true
ALERT_ERROR_RATE_THRESHOLD=5.0  # Percentage

ALERT_RESPONSE_TIME_ENABLED=true
ALERT_RESPONSE_TIME_THRESHOLD=2000.0  # Milliseconds

ALERT_MEMORY_ENABLED=true
ALERT_MEMORY_THRESHOLD=80.0  # Percentage

ALERT_CIRCUIT_BREAKER_ENABLED=true

# Monitoring Scheduler
MONITORING_EVALUATION_INTERVAL=60  # Seconds
```

### Sentry Setup

1. **Create a Sentry Account:**
   - Go to https://sentry.io
   - Sign up for a free account
   - Create a new project (select "FastAPI" as the platform)

2. **Get Your DSN:**
   - Navigate to Settings → Projects → [Your Project] → Client Keys (DSN)
   - Copy the DSN URL

3. **Configure Environment:**
   ```bash
   SENTRY_DSN=https://your-key@o123456.ingest.sentry.io/7654321
   ```

4. **Deploy:**
   - Sentry will automatically start capturing errors
   - View errors in the Sentry dashboard

## API Endpoints

### Get Metrics

```http
GET /api/v1/monitoring/metrics
```

**Response:**
```json
{
  "counters": {
    "sessions_started": 42,
    "voice_requests_total": 156,
    "errors_total": 3
  },
  "gauges": {
    "memory_usage_percent": 45.2
  },
  "histograms": {
    "workflow_duration_ms": {
      "count": 156,
      "min": 234.5,
      "max": 1823.4,
      "avg": 567.8
    }
  },
  "timestamp": "2025-10-21T12:34:56.789Z"
}
```

### Get Monitoring Status

```http
GET /api/v1/monitoring/status
```

**Response:**
```json
{
  "sentry_enabled": true,
  "alert_thresholds_count": 4,
  "active_alerts_count": 1,
  "last_evaluation": "2025-10-21T12:34:56.789Z",
  "active_alerts": [
    {
      "name": "high_error_rate",
      "severity": "critical",
      "message": "Alert: high_error_rate - error_rate_percent is 6.50 (threshold: 5.00)",
      "timestamp": "2025-10-21T12:30:00.000Z"
    }
  ]
}
```

### Get Alert History

```http
GET /api/v1/monitoring/alerts?hours=24
```

**Query Parameters:**
- `hours` - Number of hours of history (1-168, default: 24)

**Response:**
```json
[
  {
    "name": "high_error_rate",
    "severity": "critical",
    "message": "Alert: high_error_rate - error_rate_percent is 6.50 (threshold: 5.00)",
    "metric_value": 6.5,
    "threshold": 5.0,
    "timestamp": "2025-10-21T12:30:00.000Z"
  }
]
```

### Evaluate Thresholds

```http
POST /api/v1/monitoring/evaluate
```

Manually trigger threshold evaluation (useful for testing).

**Response:**
```json
{
  "evaluated": true,
  "triggered_alerts_count": 1,
  "triggered_alerts": [
    {
      "name": "high_error_rate",
      "severity": "critical",
      "message": "Alert: high_error_rate - error_rate_percent is 6.50 (threshold: 5.00)"
    }
  ]
}
```

## Railway Dashboard Integration

### Built-in Metrics

Railway provides built-in metrics in the dashboard:
- **CPU Usage** - Percentage of CPU utilized
- **Memory Usage** - RAM consumption
- **Network I/O** - Inbound/outbound traffic
- **Disk Usage** - Storage consumption

### Custom Metrics

To view custom application metrics in Railway:

1. **Use Railway Logs:**
   - All metrics are logged as structured JSON
   - Filter logs by `metric_counter`, `metric_gauge`, or `metric_histogram`
   - Example: Search for `"event":"metric_counter"` in logs

2. **Export to External Service:**
   - Use log aggregation services (Datadog, New Relic, etc.)
   - Parse JSON logs and create custom dashboards
   - Set up alerts based on log patterns

### Setting Up Alerts in Railway

Railway doesn't have built-in alerting, but you can:

1. **Use Sentry Alerts:**
   - Configure alert rules in Sentry dashboard
   - Set up notifications (email, Slack, PagerDuty)
   - Example: Alert when error rate > 5% in 5 minutes

2. **Use External Monitoring:**
   - Integrate with Datadog, New Relic, or similar
   - Set up custom alerts based on metrics
   - Configure notification channels

3. **Use Health Check Monitoring:**
   - Services like UptimeRobot, Pingdom
   - Monitor `/api/v1/health` endpoint
   - Alert on downtime or degraded status

## Alert Severity Levels

### Critical
- **high_error_rate** - Error rate exceeds threshold
- **high_memory_usage** - Memory usage exceeds threshold
- **circuit_breaker_open** - Circuit breaker has opened

**Actions:**
- Immediate investigation required
- Sent to Sentry as error-level events
- May indicate service degradation

### Warning
- **slow_response_time** - Response time exceeds threshold

**Actions:**
- Monitor for trends
- Investigate if persistent
- May indicate performance issues

## Best Practices

### 1. Threshold Tuning

Start with default thresholds and adjust based on your traffic:

```bash
# For high-traffic applications
ALERT_ERROR_RATE_THRESHOLD=2.0  # More sensitive
ALERT_RESPONSE_TIME_THRESHOLD=1000.0  # Stricter

# For low-traffic applications
ALERT_ERROR_RATE_THRESHOLD=10.0  # Less sensitive
ALERT_RESPONSE_TIME_THRESHOLD=3000.0  # More lenient
```

### 2. Alert Fatigue Prevention

- Set appropriate thresholds to avoid false positives
- Use time windows to smooth out spikes
- Disable non-critical alerts during maintenance
- Review and adjust thresholds regularly

### 3. Monitoring in Development

For local development, disable or relax alerts:

```bash
# Development .env
ALERT_ERROR_RATE_ENABLED=false
ALERT_RESPONSE_TIME_ENABLED=false
MONITORING_EVALUATION_INTERVAL=300  # 5 minutes
```

### 4. Production Monitoring Checklist

- [ ] Sentry DSN configured
- [ ] Alert thresholds tuned for your traffic
- [ ] Notification channels configured (Sentry alerts)
- [ ] Health check monitoring enabled (UptimeRobot, etc.)
- [ ] Log aggregation configured (optional)
- [ ] Dashboard bookmarked (Railway + Sentry)
- [ ] Runbook documented for common alerts

## Troubleshooting

### Sentry Not Capturing Errors

**Check:**
1. `SENTRY_DSN` is set correctly
2. `sentry-sdk` package is installed
3. No firewall blocking sentry.io
4. Check logs for "sentry_initialized" message

**Solution:**
```bash
# Verify Sentry is initialized
curl http://localhost:8080/api/v1/monitoring/status
# Check "sentry_enabled": true
```

### Alerts Not Triggering

**Check:**
1. Alert is enabled (`ALERT_*_ENABLED=true`)
2. Threshold is appropriate for your traffic
3. Monitoring scheduler is running
4. Metrics are being collected

**Solution:**
```bash
# Manually trigger evaluation
curl -X POST http://localhost:8080/api/v1/monitoring/evaluate

# Check active alerts
curl http://localhost:8080/api/v1/monitoring/alerts
```

### High Memory Usage Alerts

**Causes:**
- Too many concurrent sessions
- Memory leak in application code
- Large audio files not being cleaned up
- Qdrant client not being reused

**Solutions:**
1. Check audio cleanup job is running
2. Verify session cleanup is working
3. Monitor memory trends in Railway dashboard
4. Consider increasing memory limits

### False Positive Alerts

**Causes:**
- Threshold too sensitive
- Traffic spikes
- Deployment causing temporary issues

**Solutions:**
1. Increase threshold values
2. Increase evaluation window
3. Temporarily disable alerts during deployments

## Metrics Reference

### Session Metrics
- `sessions_started` - Total sessions created
- `session_cleanup_count` - Sessions cleaned up

### Voice Processing Metrics
- `voice_requests_total` - Total voice requests
- `voice_audio_size_bytes` - Audio file sizes
- `voice_processing_duration_ms` - Processing times

### API Call Metrics
- `api_calls_groq_success` - Successful Groq API calls
- `api_calls_groq_failure` - Failed Groq API calls
- `api_calls_elevenlabs_success` - Successful ElevenLabs calls
- `api_calls_elevenlabs_failure` - Failed ElevenLabs calls
- `api_calls_qdrant_success` - Successful Qdrant operations
- `api_calls_qdrant_failure` - Failed Qdrant operations
- `api_duration_ms_*` - API call durations

### Workflow Metrics
- `workflow_executions_success` - Successful workflow runs
- `workflow_executions_failure` - Failed workflow runs
- `workflow_duration_ms` - Workflow execution times

### Error Metrics
- `errors_total` - Total errors by type and endpoint

### System Metrics
- `memory_usage_bytes` - Memory consumption
- `memory_usage_percent` - Memory usage percentage
- `circuit_breaker_open_count` - Open circuit breakers

## Next Steps

1. **Set up Sentry** - Configure error tracking for production
2. **Tune Thresholds** - Adjust based on your traffic patterns
3. **Configure Notifications** - Set up Sentry alert rules
4. **Create Dashboard** - Bookmark Railway and Sentry dashboards
5. **Document Runbook** - Add alert response procedures
6. **Test Alerts** - Trigger test alerts to verify configuration

## Related Documentation

- [Monitoring and Observability](./MONITORING_AND_OBSERVABILITY.md) - Logging and observability
- [Operations Runbook](./OPERATIONS_RUNBOOK.md) - Troubleshooting procedures
- [Incident Response Plan](./INCIDENT_RESPONSE_PLAN.md) - Incident handling
- [Railway Setup](./RAILWAY_SETUP.md) - Deployment configuration

## Support

For issues or questions:
- Check logs: `railway logs` or Railway dashboard
- Review Sentry dashboard for errors
- Check monitoring status: `GET /api/v1/monitoring/status`
- Consult operations runbook for common issues
