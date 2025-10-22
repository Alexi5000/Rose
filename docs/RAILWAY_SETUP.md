# Railway Deployment Setup Guide

This guide provides step-by-step instructions for deploying Rose the Healer Shaman to Railway with proper configuration for production readiness.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Volume Configuration](#volume-configuration)
4. [Environment Variables](#environment-variables)
5. [Resource Limits](#resource-limits)
6. [Deployment](#deployment)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

- Railway account (sign up at https://railway.app)
- GitHub repository with the Rose application
- API keys for:
  - Groq (LLM and STT)
  - ElevenLabs (TTS)
  - Qdrant Cloud (vector database)

## Initial Setup

### 1. Create New Project

1. Log in to Railway dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your Rose repository
5. Railway will automatically detect the `railway.json` configuration

### 2. Choose Environment

Decide which environment to deploy:
- **Staging**: Use `config/railway-staging.json`
- **Production**: Use `config/railway-prod.json`

To use environment-specific config:
1. Copy the appropriate config file to root: `cp config/railway-prod.json railway.json`
2. Commit and push to trigger deployment

## Volume Configuration

Railway volumes provide persistent storage for data that must survive deployments and restarts.

### Why Volumes Are Critical

Without volumes, Rose will lose:
- All conversation history (SQLite database)
- User session data
- Backup files
- Any generated audio files not yet cleaned up

### Setting Up Volumes

1. **Navigate to Your Service**
   - In Railway dashboard, click on your deployed service
   - Go to the "Settings" tab

2. **Add Volume**
   - Scroll to "Volumes" section
   - Click "Add Volume"
   - Configure the volume:
     - **Mount Path**: `/app/data`
     - **Size**: Start with 1GB (can be increased later)
   - Click "Add"

3. **Verify Volume Mount**
   - After adding, you should see the volume listed
   - The mount path should be `/app/data`
   - Status should show as "Active"

### Volume Structure

The `/app/data` directory contains:
```
/app/data/
├── short_term_memory.db    # SQLite conversation checkpoints
├── backups/                # Automated database backups
│   ├── memory_20241021_030000.db
│   └── memory_20241022_030000.db
└── temp/                   # Temporary audio files (auto-cleaned)
```

### Volume Best Practices

1. **Monitor Usage**: Check volume usage regularly in Railway dashboard
2. **Backup Strategy**: Backups are stored in `/app/data/backups/` (7-day retention)
3. **Size Planning**: 
   - 1GB: ~10,000 conversations
   - 5GB: ~50,000 conversations
   - Scale based on usage patterns

## Environment Variables

### Required Variables

Set these in Railway dashboard under "Variables" tab:

```bash
# API Keys (REQUIRED)
GROQ_API_KEY=your_groq_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=your_voice_id

# Qdrant Configuration (REQUIRED)
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key
```

### Environment-Specific Variables

#### Staging Environment

```bash
ENVIRONMENT=staging
ALLOWED_ORIGINS=https://staging.yourdomain.com
LOG_LEVEL=INFO
ENABLE_API_DOCS=true
RATE_LIMIT_PER_MINUTE=20
SESSION_RETENTION_DAYS=3
```

#### Production Environment

```bash
ENVIRONMENT=production
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
LOG_LEVEL=INFO
ENABLE_API_DOCS=false
RATE_LIMIT_PER_MINUTE=10
SESSION_RETENTION_DAYS=7
```

### Optional Variables

```bash
# Monitoring (optional)
SENTRY_DSN=your_sentry_dsn

# Custom Configuration (optional)
WORKFLOW_TIMEOUT_SECONDS=60
MAX_REQUEST_SIZE=10485760
```

## Resource Limits

Railway automatically manages resources, but you can optimize for your plan:

### Starter Plan (512MB RAM)

- Suitable for: Development, staging, low-traffic production
- Configuration:
  - Workers: 2
  - Expected capacity: ~10-20 concurrent users
- Resource limits:
  - Memory: 512MB (Railway enforced)
  - CPU: Shared
  - Disk: 1GB volume recommended

### Developer Plan (8GB RAM)

- Suitable for: Production with moderate traffic
- Configuration:
  - Workers: 4
  - Expected capacity: ~50-100 concurrent users
- Resource limits:
  - Memory: 8GB (Railway enforced)
  - CPU: Dedicated
  - Disk: 5GB volume recommended

### Pro Plan (32GB RAM)

- Suitable for: High-traffic production
- Configuration:
  - Workers: 8
  - Expected capacity: ~200-500 concurrent users
- Resource limits:
  - Memory: 32GB (Railway enforced)
  - CPU: Dedicated with priority
  - Disk: 10GB+ volume recommended

### Resource Monitoring

1. **Check Metrics**
   - Go to "Metrics" tab in Railway dashboard
   - Monitor: CPU usage, Memory usage, Network traffic
   - Set up alerts for >80% memory usage

2. **Set Up Alerts**
   - Railway will notify you if service crashes
   - Monitor logs for memory warnings
   - Configure external monitoring (Sentry, Datadog)

3. **Optimize If Needed**
   - Reduce workers if memory usage is high
   - Increase SESSION_RETENTION_DAYS to reduce cleanup frequency
   - Consider upgrading plan if consistently hitting limits
   - Review and optimize database queries
   - Implement caching for frequently accessed data

### Health Check Grace Period

The `startPeriod` configuration gives your application time to initialize before health checks begin:

- **Default**: 40 seconds
- **Purpose**: Allows time for:
  - Python runtime initialization
  - Dependency loading
  - Database connections
  - External service verification
- **Configuration**: Set in `railway.json` under `deploy.startPeriod`

If your application takes longer to start:
1. Increase `startPeriod` to 60-90 seconds
2. Monitor startup logs to identify slow initialization
3. Optimize startup time by lazy-loading heavy dependencies

## Deployment

### Initial Deployment

1. **Trigger Build**
   - Push to your main branch
   - Railway will automatically build and deploy
   - Build time: ~5-10 minutes

2. **Monitor Build**
   - Watch build logs in Railway dashboard
   - Look for successful completion messages

3. **Wait for Health Check**
   - Railway will check `/api/health` endpoint
   - Service becomes active when health check passes
   - Initial startup: ~30-60 seconds

### Subsequent Deployments

1. **Zero-Downtime Strategy**
   - Railway keeps old instance running during deployment
   - New instance starts and passes health check
   - Traffic switches to new instance
   - Old instance shuts down

2. **Rollback Procedure**
   - If deployment fails, Railway automatically rolls back
   - Manual rollback: Go to "Deployments" tab → Click "Redeploy" on previous version

## Verification

### 1. Health Check

```bash
curl https://your-app.railway.app/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "groq": "connected",
    "elevenlabs": "connected",
    "qdrant": "connected",
    "database": "connected"
  }
}
```

### 2. API Documentation (Staging Only)

Visit: `https://your-app.railway.app/api/v1/docs`

Should show Swagger UI with all endpoints.

### 3. Test Voice Interaction

1. Open frontend: `https://your-app.railway.app`
2. Click microphone button
3. Speak a test message
4. Verify Rose responds with voice

### 4. Check Logs

```bash
# In Railway dashboard, go to "Logs" tab
# Look for:
- "Application startup complete"
- "Uvicorn running on http://0.0.0.0:8080"
- No error messages
```

### 5. Verify Data Persistence

1. Create a test session
2. Trigger a deployment (push a small change)
3. After deployment, verify session still exists
4. Check `/app/data/` volume contains database file

## Troubleshooting

### Service Won't Start

**Symptoms**: Service crashes immediately after deployment

**Solutions**:
1. Check logs for error messages
2. Verify all required environment variables are set
3. Check API keys are valid
4. Ensure Qdrant URL is accessible

### Health Check Failing

**Symptoms**: Deployment stuck on "Waiting for health check"

**Solutions**:
1. Check `/api/health` endpoint manually
2. Verify external services (Groq, ElevenLabs, Qdrant) are accessible
3. Increase `healthcheckTimeout` in railway.json
4. Check logs for connection errors

### Out of Memory

**Symptoms**: Service crashes with OOM error

**Solutions**:
1. Reduce number of workers in railway.json
2. Decrease `SESSION_RETENTION_DAYS` to reduce database size
3. Verify audio cleanup is running (check logs)
4. Upgrade to higher Railway plan

### Data Loss After Deployment

**Symptoms**: Sessions disappear after restart

**Solutions**:
1. Verify volume is properly mounted at `/app/data`
2. Check volume status in Railway dashboard
3. Ensure database path in settings points to `/app/data/`
4. Review deployment logs for volume mount errors

### Slow Response Times

**Symptoms**: API requests take >5 seconds

**Solutions**:
1. Check external API latency (Groq, ElevenLabs)
2. Verify Qdrant connection is not timing out
3. Review workflow timeout settings
4. Check for database locks (SQLite concurrency)
5. Consider migrating to PostgreSQL for better concurrency

### Rate Limiting Issues

**Symptoms**: Users getting 429 errors

**Solutions**:
1. Increase `RATE_LIMIT_PER_MINUTE` in environment variables
2. Implement user authentication for per-user limits
3. Add IP whitelist for trusted clients
4. Review rate limit logs to identify patterns

## Monitoring and Maintenance

### Daily Checks

- Review error logs for anomalies
- Check health check status
- Monitor memory usage trends

### Weekly Checks

- Review session cleanup logs
- Check backup file count
- Verify volume usage is within limits
- Review API usage and costs

### Monthly Checks

- Audit environment variables
- Review and update dependencies
- Test rollback procedure
- Review and optimize resource allocation

## Support and Resources

- **Railway Documentation**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **Project Issues**: GitHub repository issues
- **API Status**: Check Groq, ElevenLabs, Qdrant status pages

## Next Steps

After successful deployment:

1. Set up monitoring alerts (Sentry, Datadog, etc.)
2. Configure custom domain
3. Set up SSL certificate (automatic with Railway)
4. Implement backup download strategy
5. Create staging environment for testing
6. Document incident response procedures

## Configuration Files Reference

- `railway.json`: Default Railway configuration
- `config/railway-staging.json`: Staging-specific configuration
- `config/railway-prod.json`: Production-specific configuration
- `config/dev.env`: Development environment variables
- `config/staging.env`: Staging environment variables
- `config/prod.env`: Production environment variables

## Security Checklist

Before going to production:

- [ ] All API keys are set as environment variables (not in code)
- [ ] CORS origins are restricted to your domain
- [ ] API documentation is disabled (`ENABLE_API_DOCS=false`)
- [ ] Rate limiting is enabled
- [ ] Security headers are enabled
- [ ] Log level is set to INFO (not DEBUG)
- [ ] Volume is properly configured for data persistence
- [ ] Health checks are passing
- [ ] Backup strategy is in place
- [ ] Monitoring and alerting are configured
