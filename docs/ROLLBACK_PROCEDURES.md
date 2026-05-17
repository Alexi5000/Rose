# Rollback Procedures

## Overview

This document outlines procedures for rolling back deployments when issues are detected in production. Quick and safe rollbacks minimize user impact and service disruption.

## When to Rollback

### Immediate Rollback (Critical)
- Service is completely down or unreachable
- Error rate > 50%
- Data corruption detected
- Security vulnerability discovered
- Memory leaks causing repeated OOM kills

### Planned Rollback (High Priority)
- Error rate > 10% for > 5 minutes
- Response time degradation > 200% baseline
- Critical feature broken (voice processing, memory)
- External API integration failures
- Database migration failures

### Consider Rollback (Medium Priority)
- Error rate 5-10% sustained
- Performance degradation 50-100% baseline
- Non-critical feature broken
- User complaints about specific functionality

## Pre-Rollback Checklist

Before initiating rollback:

1. **Confirm the Issue**
   - [ ] Verify issue is not transient (wait 2-3 minutes)
   - [ ] Check external service status (Groq, ElevenLabs, Qdrant)
   - [ ] Review recent deployment changes
   - [ ] Confirm issue started after deployment

2. **Assess Impact**
   - [ ] Determine number of affected users
   - [ ] Identify affected functionality
   - [ ] Check if data loss is possible
   - [ ] Estimate rollback time

3. **Communication**
   - [ ] Notify team in incident channel
   - [ ] Update status page if available
   - [ ] Prepare user communication if needed

4. **Document**
   - [ ] Create incident ticket
   - [ ] Note symptoms and metrics
   - [ ] Record decision to rollback

## Railway Rollback Procedure

### Method 1: Redeploy Previous Version (Recommended)

**Time: 3-5 minutes**

1. **Access Railway Dashboard**
   ```
   Navigate to: https://railway.app/project/<project-id>
   ```

2. **View Deployment History**
   - Click on the service (e.g., "rose-api")
   - Go to "Deployments" tab
   - Identify last known good deployment

3. **Redeploy Previous Version**
   - Click on the last successful deployment
   - Click "Redeploy" button
   - Confirm redeployment

4. **Monitor Deployment**
   - Watch build logs for errors
   - Wait for health checks to pass
   - Verify service is responding

5. **Verify Rollback**
   ```bash
   # Test health endpoint
   curl https://your-app.railway.app/api/health
   
   # Test voice processing
   curl -X POST https://your-app.railway.app/api/session/start
   ```

### Method 2: Git Revert and Redeploy

**Time: 5-10 minutes**

1. **Identify Problem Commit**
   ```bash
   git log --oneline -10
   ```

2. **Revert Commit**
   ```bash
   # Revert specific commit
   git revert <commit-hash>
   
   # Or revert to specific commit
   git reset --hard <last-good-commit>
   git push --force origin main
   ```

3. **Trigger Deployment**
   - Railway will automatically detect the push
   - Monitor deployment in Railway dashboard

4. **Verify Rollback**
   - Check health endpoint
   - Test critical functionality
   - Monitor error rates

### Method 3: Environment Variable Rollback

**Time: 1-2 minutes**

If issue is caused by configuration change:

1. **Access Railway Variables**
   - Go to service settings
   - Click "Variables" tab

2. **Revert Variable**
   - Identify changed variable
   - Restore previous value
   - Click "Save"

3. **Restart Service**
   - Railway will automatically restart
   - Monitor health checks

## Docker Rollback Procedure

For self-hosted Docker deployments:

### Method 1: Use Previous Image Tag

```bash
# Stop current container
docker-compose down

# Pull previous image version
docker pull your-registry/rose-api:v1.2.3

# Update docker-compose.yml to use previous tag
# image: your-registry/rose-api:v1.2.3

# Start with previous version
docker-compose up -d

# Verify
docker ps
docker logs rose-api
curl http://localhost:8000/api/health
```

### Method 2: Rebuild from Previous Commit

```bash
# Checkout previous commit
git checkout <last-good-commit>

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Verify
docker logs rose-api
```

## Database Rollback Procedures

### SQLite Rollback

**If database migration caused issues:**

1. **Stop Service**
   ```bash
   docker-compose down
   # or Railway: pause deployment
   ```

2. **Restore from Backup**
   ```bash
   # Copy backup to active location
   cp /app/backups/short_term_memory_20251021.db \
      /app/data/short_term_memory.db
   ```

3. **Verify Database**
   ```bash
   sqlite3 /app/data/short_term_memory.db "PRAGMA integrity_check;"
   ```

4. **Restart Service**
   ```bash
   docker-compose up -d
   ```

### Qdrant Rollback

**If vector database issues:**

1. **Check Qdrant Status**
   ```bash
   curl -X GET "$QDRANT_URL/health" \
     -H "api-key: $QDRANT_API_KEY"
   ```

2. **Restore Collection from Snapshot**
   ```bash
   # Create snapshot of current state first
   curl -X POST "$QDRANT_URL/collections/rose_memories/snapshots" \
     -H "api-key: $QDRANT_API_KEY"
   
   # Restore from previous snapshot
   curl -X PUT "$QDRANT_URL/collections/rose_memories/snapshots/<snapshot-name>/recover" \
     -H "api-key: $QDRANT_API_KEY"
   ```

3. **Recreate Collection (Last Resort)**
   ```bash
   # Delete corrupted collection
   curl -X DELETE "$QDRANT_URL/collections/rose_memories" \
     -H "api-key: $QDRANT_API_KEY"
   
   # Recreate with proper schema
   # Run initialization script
   python -m ai_companion.modules.memory.initialize
   ```

## Post-Rollback Procedures

### Immediate (0-15 minutes)

1. **Verify Service Health**
   - [ ] Health endpoint returns 200 OK
   - [ ] All external services connected
   - [ ] Error rate < 1%
   - [ ] Response times normal

2. **Test Critical Paths**
   - [ ] Session creation works
   - [ ] Voice processing works
   - [ ] Memory retrieval works
   - [ ] Audio playback works

3. **Monitor Metrics**
   - [ ] Watch error rates for 15 minutes
   - [ ] Monitor response times
   - [ ] Check memory usage
   - [ ] Verify no new issues

### Short-term (15-60 minutes)

1. **Communication**
   - [ ] Update incident ticket
   - [ ] Notify team of successful rollback
   - [ ] Update status page
   - [ ] Communicate to affected users if needed

2. **Root Cause Analysis**
   - [ ] Identify what caused the issue
   - [ ] Document findings in incident ticket
   - [ ] Determine if issue was preventable
   - [ ] Identify what tests were missing

3. **Plan Forward**
   - [ ] Create fix plan for rolled-back changes
   - [ ] Add tests to prevent regression
   - [ ] Schedule fix deployment
   - [ ] Update deployment checklist

### Long-term (1-24 hours)

1. **Incident Review**
   - [ ] Conduct post-mortem meeting
   - [ ] Document lessons learned
   - [ ] Update runbooks and procedures
   - [ ] Identify process improvements

2. **Prevention**
   - [ ] Add monitoring/alerts for issue
   - [ ] Improve testing coverage
   - [ ] Update deployment checklist
   - [ ] Consider staging environment

3. **Fix and Redeploy**
   - [ ] Implement fix with tests
   - [ ] Test in development
   - [ ] Deploy to staging (if available)
   - [ ] Deploy to production with monitoring

## Rollback Decision Matrix

| Metric | Normal | Warning | Rollback |
|--------|--------|---------|----------|
| Error Rate | < 1% | 1-5% | > 5% |
| Response Time (p95) | < 2s | 2-5s | > 5s |
| Memory Usage | < 70% | 70-90% | > 90% |
| Health Check | Pass | Degraded | Fail |
| User Reports | 0-1 | 2-5 | > 5 |

## Rollback Communication Templates

### Internal Team Notification

```
🚨 ROLLBACK IN PROGRESS

Service: Rose API
Environment: Production
Reason: [Brief description]
Started: [Timestamp]
ETA: [Estimated completion]
Incident: [Ticket link]

Current Status: [In progress/Complete]
```

### User Communication (if needed)

```
We're currently experiencing technical difficulties with Rose. 
We've identified the issue and are working to restore service. 
We expect to be back online within [timeframe].

We apologize for the inconvenience.
```

### Post-Rollback Update

```
✅ ROLLBACK COMPLETE

Service: Rose API
Environment: Production
Duration: [Total time]
Impact: [Number of users/requests affected]

Service is now stable. We're investigating the root cause 
and will deploy a fix after thorough testing.

Incident Report: [Link]
```

## Testing Rollback Procedures

### Quarterly Rollback Drill

Practice rollback procedures in staging:

1. **Preparation**
   - Schedule drill with team
   - Prepare "broken" deployment
   - Set up monitoring

2. **Execute Drill**
   - Deploy broken version
   - Detect issue
   - Execute rollback procedure
   - Time each step

3. **Review**
   - Discuss what went well
   - Identify improvements
   - Update procedures
   - Train new team members

## Rollback Metrics

Track and review:
- Time to detect issue
- Time to decide on rollback
- Time to complete rollback
- Time to verify success
- Total incident duration

**Target Metrics:**
- Detection: < 5 minutes
- Decision: < 5 minutes
- Rollback: < 10 minutes
- Verification: < 5 minutes
- **Total: < 25 minutes**

## Emergency Contacts

### Internal
- On-call Engineer: [Contact]
- Engineering Manager: [Contact]
- CTO: [Contact]

### External
- Railway Support: support@railway.app
- Qdrant Support: support@qdrant.tech

## Related Documentation

- [Operations Runbook](OPERATIONS_RUNBOOK.md)
- [Incident Response Plan](INCIDENT_RESPONSE_PLAN.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Deployment Checklist](DEPLOYMENT_CHECKLIST.md)

---

**Last Updated:** October 21, 2025  
**Next Review:** January 21, 2026
