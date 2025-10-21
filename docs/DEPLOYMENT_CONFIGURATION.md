# Deployment Configuration Guide

Quick reference for configuring Rose the Healer Shaman for different deployment environments.

## Configuration Files Overview

```
config/
├── dev.env                    # Local development settings
├── staging.env                # Staging environment settings
├── prod.env                   # Production environment settings
├── railway-staging.json       # Railway staging configuration
├── railway-prod.json          # Railway production configuration
└── README.md                  # Detailed configuration documentation
```

## Quick Start

### Local Development

```bash
# Copy development configuration
cp config/dev.env .env

# Add your API keys to .env
# Then run locally
uv run uvicorn ai_companion.interfaces.web.app:app --reload
```

### Deploy to Staging

```bash
# Use staging Railway configuration
cp config/railway-staging.json railway.json

# Set environment variables in Railway dashboard from config/staging.env
# Commit and push
git add railway.json
git commit -m "Deploy to staging"
git push
```

### Deploy to Production

```bash
# Use production Railway configuration
cp config/railway-prod.json railway.json

# Set environment variables in Railway dashboard from config/prod.env
# Update ALLOWED_ORIGINS with your actual domain
# Commit and push
git add railway.json
git commit -m "Deploy to production"
git push
```

## Configuration Comparison

| Feature | Development | Staging | Production |
|---------|------------|---------|------------|
| **Logging** |
| Log Level | DEBUG | INFO | INFO |
| Log Format | console | json | json |
| **Security** |
| CORS Origins | * (all) | Restricted | Restricted |
| Rate Limiting | Disabled | 20/min | 10/min |
| Security Headers | Disabled | Enabled | Enabled |
| API Docs | Enabled | Enabled | Disabled |
| **Resources** |
| Workers | 1 | 2 | 4 |
| Timeout | 120s | 60s | 60s |
| Max Request Size | 50MB | 10MB | 10MB |
| Session Retention | 1 day | 3 days | 7 days |
| **Database** |
| Qdrant | Local | Cloud | Cloud |
| Backups | Optional | Daily | Daily |

## Environment Variables Checklist

### Required for All Environments

```bash
# AI Services
GROQ_API_KEY=                  # Groq API key for LLM and STT
ELEVENLABS_API_KEY=            # ElevenLabs API key for TTS
ELEVENLABS_VOICE_ID=           # Voice ID for Rose's voice

# Vector Database
QDRANT_URL=                    # Qdrant instance URL
QDRANT_API_KEY=                # Qdrant API key (if using cloud)
```

### Environment-Specific

#### Development
```bash
ENVIRONMENT=development
ALLOWED_ORIGINS=*
LOG_LEVEL=DEBUG
ENABLE_API_DOCS=true
RATE_LIMIT_ENABLED=false
```

#### Staging
```bash
ENVIRONMENT=staging
ALLOWED_ORIGINS=https://staging.yourdomain.com
LOG_LEVEL=INFO
ENABLE_API_DOCS=true
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=20
```

#### Production
```bash
ENVIRONMENT=production
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
LOG_LEVEL=INFO
ENABLE_API_DOCS=false
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=10
```

## Railway-Specific Configuration

### Health Checks

All environments use:
- **Path**: `/api/health`
- **Timeout**: 30 seconds
- **Interval**: 10 seconds
- **Max Retries**: 3

### Resource Allocation

#### Staging
- **Workers**: 2 uvicorn workers
- **Memory**: Recommended 512MB-1GB
- **Expected Load**: 10-20 concurrent users

#### Production
- **Workers**: 4 uvicorn workers
- **Memory**: Recommended 1GB-2GB
- **Expected Load**: 50-100 concurrent users

### Volume Configuration

**Critical**: All environments require persistent volume:
- **Mount Path**: `/app/data`
- **Minimum Size**: 1GB
- **Purpose**: SQLite database, backups, temporary files

See [Railway Setup Guide](RAILWAY_SETUP.md) for detailed volume setup.

## Docker Configuration

### Optimized Multi-Stage Build

The Dockerfile uses a 3-stage build:

1. **Frontend Builder**: Builds React application
2. **Python Builder**: Installs Python dependencies with build tools
3. **Runtime**: Minimal image with only runtime dependencies

Benefits:
- Smaller image size (~300MB vs ~1GB)
- Faster deployments
- Improved security (no build tools in production)
- Non-root user for security

### Docker Compose (Local Development)

```bash
# Start all services (Qdrant + Rose)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Security Checklist

Before deploying to production:

- [ ] All API keys set as environment variables (not in code)
- [ ] CORS origins restricted to your domain(s)
- [ ] API documentation disabled (`ENABLE_API_DOCS=false`)
- [ ] Rate limiting enabled with appropriate limits
- [ ] Security headers enabled
- [ ] Log level set to INFO (not DEBUG)
- [ ] HTTPS enabled (automatic on Railway)
- [ ] Volume configured for data persistence
- [ ] Backup strategy in place

## Monitoring Configuration

### Structured Logging

Production and staging use JSON-formatted logs for easy parsing:

```json
{
  "timestamp": "2024-10-21T10:30:00Z",
  "level": "INFO",
  "message": "Voice processing completed",
  "session_id": "abc123",
  "request_id": "xyz789",
  "duration_ms": 1234
}
```

### Health Check Response

```json
{
  "status": "healthy",
  "services": {
    "groq": "connected",
    "elevenlabs": "connected",
    "qdrant": "connected",
    "database": "connected"
  },
  "timestamp": "2024-10-21T10:30:00Z"
}
```

## Troubleshooting

### Configuration Not Applied

**Problem**: Changes to railway.json not taking effect

**Solution**:
1. Ensure railway.json is in repository root
2. Commit and push changes
3. Trigger new deployment in Railway dashboard
4. Check deployment logs for configuration errors

### Wrong Environment Detected

**Problem**: Application using wrong settings

**Solution**:
1. Check `ENVIRONMENT` variable in Railway dashboard
2. Verify it matches intended environment
3. Review logs for environment-specific behavior
4. Ensure correct railway.json is deployed

### Volume Not Persisting Data

**Problem**: Data lost after deployment

**Solution**:
1. Verify volume is mounted at `/app/data`
2. Check volume status in Railway dashboard
3. Ensure database path points to `/app/data/`
4. Review deployment logs for mount errors

## Performance Tuning

### Adjusting Workers

Workers handle concurrent requests. Adjust based on memory:

```bash
# Low memory (512MB)
--workers 1

# Medium memory (1GB)
--workers 2

# High memory (2GB+)
--workers 4
```

### Optimizing Session Retention

Reduce database size by adjusting retention:

```bash
# Development (fast cleanup)
SESSION_RETENTION_DAYS=1

# Staging (moderate retention)
SESSION_RETENTION_DAYS=3

# Production (standard retention)
SESSION_RETENTION_DAYS=7
```

### Rate Limiting

Adjust based on expected traffic:

```bash
# Low traffic
RATE_LIMIT_PER_MINUTE=10

# Medium traffic
RATE_LIMIT_PER_MINUTE=20

# High traffic (with authentication)
RATE_LIMIT_PER_MINUTE=50
```

## Additional Resources

- **[Railway Setup Guide](RAILWAY_SETUP.md)**: Comprehensive Railway deployment guide
- **[Deployment Guide](DEPLOYMENT.md)**: Multi-platform deployment instructions
- **[Operations Runbook](OPERATIONS_RUNBOOK.md)**: Troubleshooting and operations
- **[Data Persistence](DATA_PERSISTENCE.md)**: Backup and recovery procedures
- **[Config README](../config/README.md)**: Detailed configuration documentation

## Support

For deployment issues:
1. Check [Operations Runbook](OPERATIONS_RUNBOOK.md)
2. Review Railway logs
3. Verify environment variables
4. Test health endpoint
5. Open GitHub issue with logs and configuration
