# Deployment Checklist

Use this checklist before deploying Rose to production.

## Pre-Deployment Checklist

### 1. Code Quality ✅
- [x] All tests passing locally
- [x] Code formatted with Ruff
- [x] No linting errors
- [x] Type hints added to critical functions
- [x] Error handling standardized
- [x] Dependencies pinned to exact versions

### 2. Configuration ✅
- [x] Environment variables documented in `.env.example`
- [x] Configuration files organized in `config/`
- [x] Environment-specific configs (dev/staging/prod)
- [x] Railway configuration with health check grace period
- [x] Resource limits configured in Railway config
- [x] Security settings configured (CORS, rate limiting)
- [x] Logging configured (JSON format for production)
- [x] Docker image optimized (build dependencies removed)

### 3. Security ✅
- [x] No secrets in code or git history
- [x] API keys managed via environment variables
- [x] CORS restricted to specific origins
- [x] Rate limiting enabled
- [x] Security headers configured
- [x] Temporary file permissions secured

### 4. Resilience ✅
- [x] Circuit breakers implemented for external APIs
- [x] Retry logic with exponential backoff
- [x] Graceful error handling and fallbacks
- [x] Workflow timeout configured
- [x] Health check endpoint implemented

### 5. Resource Management ✅
- [x] Memory limits configured
- [x] Audio file cleanup scheduled
- [x] Session cleanup configured (7 days)
- [x] Database connection pooling
- [x] Request size limits set

### 6. Monitoring & Observability ✅
- [x] Structured logging (JSON format)
- [x] Request ID tracking
- [x] Health check with dependency verification
- [x] Error logging with context
- [x] Performance metrics available

### 7. Data Persistence ✅
- [x] SQLite checkpointer for conversation state
- [x] Qdrant for long-term memory
- [x] Backup strategy documented
- [x] Data retention policy configured
- [x] Volume configuration documented

### 8. Testing ✅
- [x] Unit tests passing
- [x] Integration tests passing
- [x] Circuit breaker tests passing
- [x] Smoke tests passing
- [x] Deployment tests passing

### 9. Documentation ✅
- [x] README.md updated
- [x] API documentation complete
- [x] Deployment guide available
- [x] Operations runbook created
- [x] Incident response plan documented
- [x] Rollback procedures documented

### 10. Project Organization ✅
- [x] Root folder cleaned and organized
- [x] Files in logical subdirectories
- [x] Project structure documented
- [x] All references updated

## Deployment Steps

### Step 1: Prepare Environment
```bash
# 1. Ensure all environment variables are set
cp .env.example .env
# Edit .env with your actual API keys

# 2. Verify configuration
cat config/railway.json
```

### Step 2: Run Tests
```bash
# Run all tests
./scripts/run_tests.sh all

# Or on Windows
scripts\run_tests.bat all

# Verify no failures
```

### Step 3: Build and Test Locally
```bash
# Build Docker image
docker build -t rose-api .

# Test the build
docker run -p 8080:8080 --env-file .env rose-api

# Verify health check
curl http://localhost:8080/api/health
```

### Step 4: Deploy to Railway

#### Option A: Via GitHub (Recommended)
```bash
# 1. Push to GitHub
git push origin main

# 2. Railway will auto-deploy from GitHub
# Monitor deployment in Railway dashboard
```

#### Option B: Via Railway CLI
```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Link project
railway link

# 4. Deploy
railway up
```

### Step 5: Configure Railway

1. **Choose Configuration**
   - For staging: `cp config/railway-staging.json railway.json`
   - For production: `cp config/railway-prod.json railway.json`
   - See [DEPLOYMENT_CONFIGURATION.md](DEPLOYMENT_CONFIGURATION.md) for details

2. **Add Persistent Volume**
   - Go to Railway dashboard
   - Select your service
   - Settings → Volumes → Add Volume
   - Mount path: `/app/data`
   - Size: 1GB (staging) or 5GB (production)
   - Redeploy after adding volume
   - See [RAILWAY_SETUP.md](RAILWAY_SETUP.md#volume-configuration) for detailed steps

3. **Set Environment Variables**
   - Copy from `config/staging.env` or `config/prod.env`
   - Set in Railway dashboard under Variables tab
   - Update `ALLOWED_ORIGINS` with your actual domain(s)
   - Verify all required API keys are set

4. **Configure Resource Limits** (Optional)
   - Railway automatically manages resources
   - Monitor usage in Metrics tab
   - Adjust workers in railway.json if needed
   - See [DEPLOYMENT_CONFIGURATION.md](DEPLOYMENT_CONFIGURATION.md#resource-limits)

5. **Configure Custom Domain** (Optional)
   - Add custom domain in Railway
   - Update DNS records
   - Update `ALLOWED_ORIGINS` environment variable
   - SSL certificate is automatic

### Step 6: Verify Deployment

```bash
# 1. Check health endpoint
curl https://your-app.railway.app/api/health

# 2. Check API documentation
open https://your-app.railway.app/api/v1/docs

# 3. Test voice endpoint
# Use frontend or Postman to test /api/voice/process

# 4. Check logs
railway logs
```

### Step 7: Post-Deployment Monitoring

1. **Monitor Logs**
   ```bash
   railway logs --follow
   ```

2. **Check Metrics**
   - Memory usage
   - Response times
   - Error rates
   - Request volume

3. **Test Critical Paths**
   - Voice recording and playback
   - Session creation
   - Memory persistence
   - Error handling

## Rollback Procedure

If deployment fails or issues are detected:

### Quick Rollback
```bash
# 1. Revert to previous deployment in Railway dashboard
# Settings → Deployments → Select previous → Redeploy

# 2. Or rollback git commit
git revert HEAD
git push origin main
```

### Full Rollback
See [ROLLBACK_PROCEDURES.md](ROLLBACK_PROCEDURES.md) for detailed steps.

## Post-Deployment Tasks

### Immediate (Within 1 hour)
- [ ] Verify all endpoints responding
- [ ] Test voice interaction flow
- [ ] Check error logs for issues
- [ ] Monitor memory usage
- [ ] Verify external API connectivity

### Short-term (Within 24 hours)
- [ ] Monitor error rates
- [ ] Check session persistence
- [ ] Verify memory cleanup running
- [ ] Test from multiple devices
- [ ] Gather initial user feedback

### Medium-term (Within 1 week)
- [ ] Review performance metrics
- [ ] Analyze usage patterns
- [ ] Optimize based on real data
- [ ] Update documentation with learnings
- [ ] Plan next iteration

## Troubleshooting

### Deployment Fails
1. Check Railway logs for errors
2. Verify environment variables are set
3. Check Docker build succeeds locally
4. Review `config/railway.json` configuration

### Health Check Fails
1. Verify external API keys are valid
2. Check Qdrant connectivity
3. Increase health check timeout
4. Review logs for connection errors

### High Memory Usage
1. Check session count
2. Verify audio cleanup is running
3. Review memory retention settings
4. Consider upgrading Railway plan

### Slow Response Times
1. Check external API latency
2. Review circuit breaker status
3. Monitor concurrent requests
4. Check database query performance

## Support Resources

- **Documentation**: [docs/](.)
- **Operations Runbook**: [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md)
- **Incident Response**: [INCIDENT_RESPONSE_PLAN.md](INCIDENT_RESPONSE_PLAN.md)
- **Railway Docs**: https://docs.railway.app
- **Project Issues**: GitHub Issues

## Success Criteria

Deployment is successful when:
- ✅ Health check returns 200 OK
- ✅ All external services connected
- ✅ Voice interaction works end-to-end
- ✅ Sessions persist across requests
- ✅ Memory system functioning
- ✅ Error rate < 1%
- ✅ Response time < 5 seconds
- ✅ No critical errors in logs

---

**Last Updated**: After root folder cleanup and code quality improvements  
**Version**: 1.0  
**Status**: Production Ready ✅
