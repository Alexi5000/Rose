# Configuration Files

This directory contains environment-specific configuration files for deploying Rose the Healer Shaman to different environments.

## Environment Files

### Development (`dev.env`)

Use for local development:
- Relaxed security settings
- Verbose logging (DEBUG level)
- API documentation enabled
- No rate limiting
- Local Qdrant instance

**Usage**:
```bash
cp config/dev.env .env
# Edit .env with your API keys

# Start development servers (recommended)
python scripts/run_dev_server.py

# Or start backend only
uv run uvicorn ai_companion.interfaces.web.app:app --reload --port 8000
```

### Staging (`staging.env`)

Use for staging/testing environment:
- Moderate security settings
- Structured logging (INFO level)
- API documentation enabled for testing
- Moderate rate limiting
- Qdrant Cloud instance
- Shorter session retention (3 days)

**Usage**:
```bash
# In Railway dashboard, set environment variables from staging.env
# Or use railway-staging.json configuration
```

### Production (`prod.env`)

Use for production deployment:
- Strict security settings
- Structured logging (INFO level)
- API documentation disabled
- Strict rate limiting
- Qdrant Cloud instance
- Standard session retention (7 days)

**Usage**:
```bash
# In Railway dashboard, set environment variables from prod.env
# Or use railway-prod.json configuration
```

## Railway Configuration Files

### Default (`railway.json` in root)

Basic Railway configuration with:
- Health check configuration with 40s grace period
- Build and start commands
- Restart policy
- 2 workers for balanced performance

### Staging (`railway-staging.json`)

Staging-specific Railway configuration:
- 2 workers (optimized for 512MB-2GB RAM)
- Staging environment variables
- API docs enabled for testing
- Moderate rate limiting (20 req/min)
- Health check grace period: 40 seconds
- Restart policy: ON_FAILURE with 3 retries

**Usage**:
```bash
cp config/railway-staging.json railway.json
git add railway.json
git commit -m "Configure for staging"
git push
```

**Resource Requirements**:
- Minimum RAM: 512MB
- Recommended RAM: 1-2GB
- Volume: 1GB
- Expected capacity: 10-20 concurrent users

### Production (`railway-prod.json`)

Production-specific Railway configuration:
- 4 workers (optimized for 4-8GB RAM)
- Production environment variables
- API docs disabled for security
- Strict rate limiting (10 req/min)
- Health check grace period: 40 seconds
- Restart policy: ON_FAILURE with 3 retries

**Usage**:
```bash
cp config/railway-prod.json railway.json
git add railway.json
git commit -m "Configure for production"
git push
```

**Resource Requirements**:
- Minimum RAM: 2GB
- Recommended RAM: 4-8GB
- Volume: 5GB
- Expected capacity: 50-100 concurrent users

### Health Check Configuration

All Railway configurations include:
- **Health Check Path**: `/api/health`
- **Timeout**: 30 seconds per check
- **Interval**: 10 seconds between checks
- **Start Period**: 40 seconds grace period before first check
- **Restart Policy**: Restart on failure, max 3 retries

The start period (grace period) is critical for:
1. Allowing Python runtime to initialize
2. Loading dependencies and models
3. Establishing database connections
4. Verifying external service connectivity

If your application needs more startup time, increase `startPeriod` in railway.json.

## Configuration Differences

| Setting | Development | Staging | Production |
|---------|------------|---------|------------|
| Log Level | DEBUG | INFO | INFO |
| Log Format | console | json | json |
| API Docs | Enabled | Enabled | Disabled |
| Rate Limiting | Disabled | 20/min | 10/min |
| Security Headers | Disabled | Enabled | Enabled |
| CORS Origins | * | Restricted | Restricted |
| Session Retention | 1 day | 3 days | 7 days |
| Workers | 1 | 2 | 4 |

## Environment Variables

All environment files require these API keys:

```bash
# Required
GROQ_API_KEY=your_groq_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=your_voice_id
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
```

See individual `.env` files for complete variable lists.

## Best Practices

1. **Never commit `.env` files**: Keep API keys secret
2. **Use Railway environment variables**: Set secrets in Railway dashboard
3. **Test in staging first**: Always test changes in staging before production
4. **Monitor resource usage**: Adjust workers based on memory usage
5. **Update CORS origins**: Replace placeholder domains with actual domains
6. **Review logs regularly**: Check for errors and performance issues

## Switching Environments

### Local Development → Staging

1. Copy staging configuration:
   ```bash
   cp config/railway-staging.json railway.json
   ```

2. Set environment variables in Railway dashboard from `config/staging.env`

3. Commit and push:
   ```bash
   git add railway.json
   git commit -m "Deploy to staging"
   git push
   ```

### Staging → Production

1. Copy production configuration:
   ```bash
   cp config/railway-prod.json railway.json
   ```

2. Update environment variables in Railway dashboard from `config/prod.env`

3. Update CORS origins to production domains

4. Commit and push:
   ```bash
   git add railway.json
   git commit -m "Deploy to production"
   git push
   ```

## Troubleshooting

### Configuration Not Applied

- Verify environment variables are set in Railway dashboard
- Check Railway logs for configuration errors
- Ensure railway.json is in repository root
- Trigger new deployment after configuration changes

### Wrong Environment Detected

- Check `ENVIRONMENT` variable in Railway dashboard
- Verify it matches your intended environment (development/staging/production)
- Review logs for environment-specific behavior

### Resource Limits Exceeded

- Reduce number of workers in railway.json
- Decrease session retention days
- Upgrade Railway plan
- Optimize memory usage

## Additional Resources

- [Railway Setup Guide](../docs/RAILWAY_SETUP.md)
- [Deployment Documentation](../docs/DEPLOYMENT.md)
- [Operations Runbook](../docs/OPERATIONS_RUNBOOK.md)
