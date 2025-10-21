# Rollback Procedures: Rose the Healer Shaman

This document provides step-by-step procedures for rolling back deployments and restoring data in case of issues.

## Table of Contents

- [Overview](#overview)
- [Deployment Rollback](#deployment-rollback)
  - [Railway Rollback](#railway-rollback)
  - [Render Rollback](#render-rollback)
  - [Fly.io Rollback](#flyio-rollback)
- [Data Restoration](#data-restoration)
  - [Database Restoration](#database-restoration)
  - [Manual Backup Restoration](#manual-backup-restoration)
- [Rollback Decision Matrix](#rollback-decision-matrix)
- [Post-Rollback Procedures](#post-rollback-procedures)
- [Prevention Strategies](#prevention-strategies)

---

## Overview

### When to Rollback

Consider rollback when:
- **Critical bugs** affecting core functionality
- **Data corruption** or loss
- **Performance degradation** > 50% from baseline
- **Error rate** > 10% for more than 5 minutes
- **Security vulnerabilities** discovered in new deployment
- **External service incompatibility** introduced

### Rollback Types

1. **Code Rollback**: Revert to previous application version
2. **Data Rollback**: Restore database from backup
3. **Configuration Rollback**: Revert environment variables or settings
4. **Full Rollback**: Combination of code and data rollback

### Rollback Time Targets

- **Detection to Decision**: < 5 minutes
- **Decision to Execution**: < 2 minutes
- **Execution to Verification**: < 5 minutes
- **Total Rollback Time**: < 15 minutes

---

## Deployment Rollback

### Railway Rollback

Railway maintains deployment history and allows instant rollback to previous versions.

#### Quick Rollback (Recommended)

1. **Access Deployment History**
   - Go to Railway dashboard
   - Navigate to your service
   - Click on "Deployments" tab

2. **Identify Last Known Good Deployment**
   - Review deployment list
   - Find deployment before issues started
   - Note the deployment ID and timestamp

3. **Rollback to Previous Deployment**
   - Click on the last known good deployment
   - Click "Redeploy" button
   - Confirm rollback action

4. **Monitor Rollback**
   - Watch deployment logs
   - Wait for "Deployment successful" message
   - Typically takes 2-3 minutes

5. **Verify Service Health**
   ```bash
   curl https://your-app.railway.app/api/health
   ```

#### CLI Rollback

```bash
# List recent deployments
railway deployments

# Rollback to specific deployment
railway rollback <deployment-id>

# Monitor rollback progress
railway logs --tail 100
```

#### Git-Based Rollback

If you need to rollback code changes:

```bash
# Identify commit to rollback to
git log --oneline -10

# Create rollback commit
git revert <bad-commit-hash>

# Or reset to previous commit (use with caution)
git reset --hard <good-commit-hash>

# Force push (if necessary)
git push origin main --force

# Railway will auto-deploy the rollback
```

**Warning**: Force pushing can cause issues for other developers. Prefer `git revert` for shared branches.

---

### Render Rollback

Render also maintains deployment history with easy rollback.

#### Dashboard Rollback

1. **Access Deployment History**
   - Go to Render dashboard
   - Select your service
   - Click "Deploys" tab

2. **Select Previous Deployment**
   - Find last known good deployment
   - Click "Rollback to this deploy"

3. **Confirm Rollback**
   - Review deployment details
   - Click "Rollback" to confirm
   - Wait for deployment to complete (3-5 minutes)

4. **Verify Service**
   ```bash
   curl https://your-app.onrender.com/api/health
   ```

#### Manual Redeploy

If rollback button is unavailable:

```bash
# Trigger manual deploy from specific commit
git checkout <good-commit-hash>
git push render main --force
```

---

### Fly.io Rollback

Fly.io uses image-based deployments with version history.

#### CLI Rollback

```bash
# List deployment history
fly releases

# Rollback to previous release
fly releases rollback

# Or rollback to specific version
fly releases rollback <version-number>

# Monitor rollback
fly logs
```

#### Verify Rollback

```bash
# Check current version
fly status

# Test health endpoint
curl https://your-app.fly.dev/api/health
```

---

## Data Restoration

### Database Restoration

The application includes automatic backup functionality. Follow these steps to restore from backup.

#### Automatic Backup Restoration

1. **Identify Available Backups**
   
   Backups are stored in `/app/data/backups/` with naming pattern:
   - `memory_YYYYMMDD_HHMMSS.db` (SQLite backups)
   - `backup.log` (backup operation logs)

2. **Access Backup Files**
   
   **Railway:**
   ```bash
   # SSH into container (if available)
   railway run bash
   
   # List available backups
   ls -lh /app/data/backups/
   ```
   
   **Alternative: Download via API**
   - Create temporary endpoint to download backups
   - Or use Railway's file browser (if available)

3. **Stop Application**
   ```bash
   railway down
   ```

4. **Restore Database**
   ```bash
   # Copy backup to active database location
   cp /app/data/backups/memory_20240115_020000.db /app/data/memory.db
   
   # Verify file integrity
   sqlite3 /app/data/memory.db "PRAGMA integrity_check;"
   ```

5. **Restart Application**
   ```bash
   railway up
   ```

6. **Verify Restoration**
   - Test session creation
   - Verify conversation history
   - Check memory retrieval

#### Manual Backup Restoration

If you have manual backups stored externally:

1. **Download Backup File**
   ```bash
   # Download from your backup storage
   wget https://your-backup-storage.com/memory_backup.db
   ```

2. **Upload to Railway**
   ```bash
   # Use Railway CLI to upload
   railway run --command "cat > /app/data/memory.db" < memory_backup.db
   ```

3. **Restart and Verify**
   ```bash
   railway restart
   curl https://your-app.railway.app/api/health
   ```

---

### Qdrant Data Restoration

Qdrant (long-term memory) restoration depends on your Qdrant setup.

#### Qdrant Cloud Restoration

1. **Contact Qdrant Support**
   - Email: support@qdrant.io
   - Request point-in-time restoration
   - Provide cluster ID and timestamp

2. **Alternative: Recreate Collection**
   ```python
   # If you have conversation history, rebuild vectors
   from ai_companion.modules.memory.long_term_memory import LongTermMemory
   
   memory = LongTermMemory()
   # Rebuild from conversation logs
   ```

#### Self-Hosted Qdrant Restoration

1. **Stop Qdrant Service**
   ```bash
   docker stop qdrant
   ```

2. **Restore Snapshot**
   ```bash
   # Copy snapshot to Qdrant storage directory
   cp qdrant_snapshot.tar.gz /path/to/qdrant/storage/
   
   # Extract snapshot
   cd /path/to/qdrant/storage/
   tar -xzf qdrant_snapshot.tar.gz
   ```

3. **Restart Qdrant**
   ```bash
   docker start qdrant
   ```

---

## Rollback Decision Matrix

Use this matrix to determine the appropriate rollback strategy:

| Issue Type | Severity | Code Rollback | Data Rollback | Downtime | Priority |
|------------|----------|---------------|---------------|----------|----------|
| Critical bug | High | Yes | No | < 5 min | P0 |
| Data corruption | Critical | Maybe | Yes | < 15 min | P0 |
| Performance degradation | Medium | Yes | No | < 5 min | P1 |
| Minor bug | Low | No | No | 0 min | P2 |
| Config error | Medium | No | No | < 2 min | P1 |
| Security issue | Critical | Yes | Maybe | < 5 min | P0 |
| External API incompatibility | High | Yes | No | < 5 min | P0 |

### Decision Flowchart

```
Issue Detected
    ↓
Is it affecting users?
    ↓ Yes                    ↓ No
Is error rate > 10%?     Monitor and fix
    ↓ Yes                    in next release
Is there data loss?
    ↓ Yes                ↓ No
Full Rollback        Code Rollback
(Code + Data)        Only
    ↓                    ↓
Execute Rollback     Execute Rollback
    ↓                    ↓
Verify Health        Verify Health
    ↓                    ↓
Post-Mortem          Post-Mortem
```

---

## Post-Rollback Procedures

### Immediate Verification (< 5 minutes)

1. **Health Check**
   ```bash
   curl https://your-app.railway.app/api/health
   ```
   
   Expected: All services "healthy"

2. **Smoke Test**
   - Create new session
   - Send test voice input
   - Verify response generation
   - Check audio playback

3. **Monitor Error Rate**
   ```bash
   railway logs | grep "ERROR" | wc -l
   ```
   
   Expected: < 1% error rate

4. **Check Key Metrics**
   - Response time < 5 seconds
   - Memory usage stable
   - No circuit breaker alerts

### Short-Term Actions (< 1 hour)

1. **Notify Stakeholders**
   - Inform team of rollback
   - Update status page
   - Communicate with affected users

2. **Document Incident**
   - Record timeline of events
   - Note symptoms and impact
   - Document rollback steps taken

3. **Identify Root Cause**
   - Review failed deployment changes
   - Analyze logs from failed deployment
   - Identify what went wrong

4. **Create Fix Plan**
   - Determine proper fix
   - Plan testing strategy
   - Schedule fix deployment

### Long-Term Actions (< 1 week)

1. **Conduct Post-Mortem**
   - See [Incident Response Plan](INCIDENT_RESPONSE_PLAN.md)
   - Identify contributing factors
   - Document lessons learned

2. **Implement Preventive Measures**
   - Add tests to catch similar issues
   - Improve deployment checks
   - Update monitoring/alerts

3. **Deploy Fix**
   - Implement proper fix
   - Test thoroughly in staging
   - Deploy with extra monitoring

4. **Update Documentation**
   - Update runbooks if needed
   - Document new failure mode
   - Share learnings with team

---

## Prevention Strategies

### Pre-Deployment Checks

1. **Automated Testing**
   - Run full test suite
   - Check code coverage
   - Verify integration tests pass

2. **Staging Deployment**
   - Deploy to staging first
   - Run smoke tests
   - Monitor for 30 minutes

3. **Deployment Checklist**
   - [ ] All tests passing
   - [ ] Code review completed
   - [ ] Environment variables verified
   - [ ] Database migrations tested
   - [ ] Rollback plan documented
   - [ ] Monitoring alerts configured

### Deployment Best Practices

1. **Gradual Rollout**
   - Deploy to single instance first
   - Monitor for issues
   - Gradually increase traffic

2. **Feature Flags**
   - Use feature flags for risky changes
   - Enable for small percentage of users
   - Gradually increase rollout

3. **Canary Deployments**
   - Deploy to small subset of infrastructure
   - Compare metrics with stable version
   - Proceed only if metrics are good

4. **Blue-Green Deployments**
   - Maintain two identical environments
   - Deploy to inactive environment
   - Switch traffic after verification

### Monitoring During Deployment

1. **Watch Key Metrics**
   - Error rate
   - Response time
   - Memory usage
   - Active sessions

2. **Set Deployment Alerts**
   - Alert on error rate > 2%
   - Alert on response time > 8s
   - Alert on health check failures

3. **Have Rollback Ready**
   - Keep rollback command ready
   - Monitor for 15 minutes post-deployment
   - Be prepared to rollback quickly

---

## Rollback Testing

### Regular Rollback Drills

Conduct rollback drills quarterly to ensure procedures work:

1. **Schedule Drill**
   - Choose low-traffic time
   - Notify team in advance
   - Prepare test scenarios

2. **Execute Rollback**
   - Follow documented procedures
   - Time each step
   - Note any issues

3. **Verify Success**
   - Run full smoke tests
   - Check all functionality
   - Verify data integrity

4. **Document Results**
   - Update procedures if needed
   - Note time taken
   - Identify improvements

### Rollback Checklist

Use this checklist during actual rollbacks:

- [ ] Issue severity assessed
- [ ] Rollback decision made
- [ ] Stakeholders notified
- [ ] Last known good version identified
- [ ] Rollback command prepared
- [ ] Monitoring dashboard open
- [ ] Rollback executed
- [ ] Health check passed
- [ ] Smoke tests passed
- [ ] Error rate normal
- [ ] Users notified
- [ ] Incident documented
- [ ] Post-mortem scheduled

---

## Emergency Contacts

### Internal Escalation
- **On-Call Engineer**: [Contact info]
- **Engineering Lead**: [Contact info]
- **CTO/VP Engineering**: [Contact info]

### External Support
- **Railway Support**: help@railway.app
- **Groq Support**: support@groq.com
- **ElevenLabs Support**: support@elevenlabs.io
- **Qdrant Support**: support@qdrant.io

---

## Related Documentation

- [Operations Runbook](OPERATIONS_RUNBOOK.md)
- [Incident Response Plan](INCIDENT_RESPONSE_PLAN.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Data Persistence Guide](DATA_PERSISTENCE.md)

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2024-01-15 | 1.0 | Initial rollback procedures |
