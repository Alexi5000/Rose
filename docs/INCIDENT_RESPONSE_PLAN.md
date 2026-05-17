# Incident Response Plan

## Overview

This document defines the incident response process for the Rose the Healer Shaman application. It provides a structured approach to detecting, responding to, and resolving production incidents while minimizing user impact.

## Incident Severity Levels

### SEV-1: Critical

**Definition:** Complete service outage or critical functionality broken affecting all users.

**Examples:**
- Service completely down or unreachable
- Database corruption causing data loss
- Security breach or data leak
- All voice processing failing
- Error rate > 50%

**Response Time:** Immediate (< 15 minutes)  
**Communication:** Immediate notification to all stakeholders  
**Escalation:** Automatic to engineering manager and CTO

### SEV-2: High

**Definition:** Major functionality degraded affecting many users.

**Examples:**
- Significant performance degradation (> 200% baseline)
- Critical feature broken (voice, memory, sessions)
- Error rate 10-50%
- External API integration failures
- Repeated service restarts

**Response Time:** < 30 minutes  
**Communication:** Notify team and stakeholders within 15 minutes  
**Escalation:** To engineering manager if not resolved in 1 hour

### SEV-3: Medium

**Definition:** Partial functionality impaired affecting some users.

**Examples:**
- Non-critical feature broken
- Performance degradation 50-100% baseline
- Error rate 5-10%
- Intermittent failures
- Single external service degraded

**Response Time:** < 1 hour  
**Communication:** Notify team within 30 minutes  
**Escalation:** To engineering manager if not resolved in 4 hours

### SEV-4: Low

**Definition:** Minor issues with minimal user impact.

**Examples:**
- Cosmetic UI issues
- Non-critical logging errors
- Error rate 1-5%
- Documentation issues
- Minor performance degradation

**Response Time:** < 4 hours  
**Communication:** Log in incident tracker  
**Escalation:** None unless pattern emerges

## Incident Response Phases

### 1. Detection

**Automated Detection:**
- Monitoring alerts (error rate, response time, memory)
- Health check failures
- External service status changes
- Log pattern detection

**Manual Detection:**
- User reports
- Team member observation
- Support tickets
- Social media mentions

**Actions:**
1. Acknowledge alert/report
2. Verify issue is real (not false positive)
3. Assess initial severity
4. Create incident ticket

### 2. Response

**Immediate Actions (0-5 minutes):**

1. **Acknowledge Incident**
   - Create incident ticket with severity
   - Assign incident commander (on-call engineer)
   - Start incident timeline

2. **Initial Assessment**
   - Check service health: `curl https://app.railway.app/api/health`
   - Review recent deployments
   - Check external service status
   - Review error logs

3. **Communicate**
   - Post in incident channel: `#incidents`
   - Use incident template (see below)
   - Tag relevant team members

**Investigation Actions (5-15 minutes):**

1. **Gather Data**
   ```bash
   # Check error logs
   grep "ERROR" /app/logs/app.log | tail -100
   
   # Check system resources
   docker stats
   
   # Check database
   sqlite3 /app/data/short_term_memory.db "SELECT COUNT(*) FROM checkpoints;"
   
   # Test external APIs
   curl https://api.groq.com/health
   curl https://api.elevenlabs.io/health
   ```

2. **Identify Root Cause**
   - Recent code changes?
   - Configuration changes?
   - External service issues?
   - Resource exhaustion?
   - Database issues?

3. **Determine Response Strategy**
   - Can we fix forward quickly (< 15 min)?
   - Should we rollback?
   - Do we need to scale resources?
   - Should we enable degraded mode?

### 3. Mitigation

**Quick Fixes (if possible):**

1. **Configuration Fix**
   - Revert environment variable
   - Adjust resource limits
   - Enable/disable feature flag

2. **Service Restart**
   - Clear memory leaks
   - Reload configuration
   - Reset connections

3. **External Service Workaround**
   - Switch to backup provider
   - Enable circuit breaker
   - Use cached responses

**Rollback (if needed):**

Follow [Rollback Procedures](ROLLBACK_PROCEDURES.md):
1. Confirm rollback decision
2. Execute rollback
3. Verify service health
4. Monitor for stability

**Scaling (if needed):**

1. Increase memory limits
2. Add more instances (if supported)
3. Enable request queuing
4. Implement rate limiting

### 4. Recovery

**Verification (0-15 minutes after mitigation):**

1. **Health Checks**
   - [ ] Service responding to health endpoint
   - [ ] All external services connected
   - [ ] Error rate < 1%
   - [ ] Response times normal

2. **Functional Testing**
   - [ ] Session creation works
   - [ ] Voice processing works
   - [ ] Memory retrieval works
   - [ ] Audio playback works

3. **Monitoring**
   - Watch metrics for 15 minutes
   - Verify no regression
   - Check for side effects

**Communication:**
- Update incident channel with resolution
- Update status page
- Notify affected users if needed
- Thank team members

### 5. Post-Incident

**Immediate (0-1 hour):**

1. **Document Incident**
   - Update incident ticket with timeline
   - Record root cause
   - Note mitigation steps taken
   - List affected users/requests

2. **Communicate Resolution**
   - Post resolution in incident channel
   - Update stakeholders
   - Close incident ticket

**Short-term (1-24 hours):**

1. **Create Action Items**
   - Immediate fixes needed
   - Tests to add
   - Monitoring to improve
   - Documentation to update

2. **Schedule Post-Mortem**
   - Within 48 hours for SEV-1/SEV-2
   - Within 1 week for SEV-3
   - Optional for SEV-4

**Long-term (1-7 days):**

1. **Conduct Post-Mortem**
   - Review timeline
   - Identify root cause
   - Discuss what went well
   - Identify improvements
   - Create action items

2. **Implement Improvements**
   - Add monitoring/alerts
   - Improve testing
   - Update runbooks
   - Train team

## Incident Communication

### Internal Communication Template

**Initial Notification:**
```
🚨 INCIDENT: [Brief Description]

Severity: SEV-[1/2/3/4]
Status: Investigating
Started: [Timestamp]
Incident Commander: @[Name]
Ticket: [Link]

Impact:
- [Description of user impact]
- [Affected functionality]

Current Actions:
- [What we're doing now]

Updates: Will provide update in 15 minutes
```

**Status Update:**
```
📊 INCIDENT UPDATE: [Brief Description]

Status: [Investigating/Mitigating/Resolved]
Time Elapsed: [Duration]

Progress:
- [What we've learned]
- [What we've tried]
- [Current status]

Next Steps:
- [What we're doing next]

Next Update: [Timeframe]
```

**Resolution:**
```
✅ INCIDENT RESOLVED: [Brief Description]

Duration: [Total time]
Root Cause: [Brief explanation]
Resolution: [What fixed it]

Impact:
- Users affected: [Number/percentage]
- Requests failed: [Number]
- Data loss: [None/Description]

Follow-up:
- Post-mortem scheduled: [Date/time]
- Action items: [Link]

Thank you to: @[Team members]
```

### External Communication Template

**Status Page Update:**
```
We're currently investigating reports of [issue description]. 
Some users may experience [specific impact]. 

We're actively working on a resolution and will provide 
updates every 30 minutes.

Last updated: [Timestamp]
```

**User Notification (if needed):**
```
Subject: Service Disruption - [Date]

We experienced a service disruption today from [start time] 
to [end time] that affected [description of impact].

What happened:
[Brief, non-technical explanation]

What we did:
[Brief explanation of resolution]

What we're doing to prevent this:
[Brief explanation of improvements]

We sincerely apologize for the inconvenience.

- The Rose Team
```

## Incident Roles and Responsibilities

### Incident Commander (On-call Engineer)

**Responsibilities:**
- Lead incident response
- Make decisions on mitigation strategy
- Coordinate team members
- Communicate status updates
- Ensure documentation

**Authority:**
- Can make deployment decisions
- Can rollback without approval
- Can escalate to management
- Can request additional resources

### Technical Responders

**Responsibilities:**
- Investigate root cause
- Implement fixes
- Test solutions
- Monitor systems

**Who:**
- Backend engineers
- DevOps engineers
- Database specialists (if needed)

### Communications Lead (for SEV-1/SEV-2)

**Responsibilities:**
- Update status page
- Communicate with stakeholders
- Draft user notifications
- Coordinate with support team

**Who:**
- Product manager
- Engineering manager
- Customer support lead

## Escalation Procedures

### When to Escalate

**To Engineering Manager:**
- SEV-1 incidents (automatic)
- SEV-2 not resolved in 1 hour
- SEV-3 not resolved in 4 hours
- Need additional resources
- Unclear mitigation strategy

**To CTO:**
- SEV-1 not resolved in 1 hour
- Security incidents
- Data loss incidents
- Need executive decision
- External communication needed

**To External Support:**
- External service issues (Groq, ElevenLabs, Qdrant)
- Platform issues (Railway)
- Need vendor assistance

### Escalation Contacts

**Internal:**
- On-call Engineer: [Pager/Phone]
- Secondary Engineer: [Pager/Phone]
- Engineering Manager: [Phone/Slack]
- CTO: [Phone/Slack]

**External:**
- Groq Support: support@groq.com
- ElevenLabs Support: support@elevenlabs.io
- Qdrant Support: support@qdrant.tech
- Railway Support: support@railway.app

## Incident Response Tools

### Monitoring and Alerting
- Railway dashboard: https://railway.app
- Health check endpoint: /api/health
- Log aggregation: Railway logs
- Metrics: Railway metrics

### Communication
- Incident channel: #incidents (Slack)
- Status page: [URL if available]
- Incident tracker: [GitHub Issues/Jira]

### Documentation
- Operations Runbook: [Link](OPERATIONS_RUNBOOK.md)
- Rollback Procedures: [Link](ROLLBACK_PROCEDURES.md)
- Deployment Guide: [Link](DEPLOYMENT.md)

### Access
- Railway dashboard access
- Database access (read-only for investigation)
- Log access
- Monitoring dashboard access

## Common Incident Scenarios

### Scenario 1: Complete Service Outage

**Symptoms:** Service unreachable, health checks failing

**Response:**
1. Check Railway service status
2. Check recent deployments
3. Review startup logs
4. Rollback if recent deployment
5. Restart service if configuration issue
6. Escalate if platform issue

**Typical Resolution Time:** 10-20 minutes

### Scenario 2: High Error Rate

**Symptoms:** Error rate > 10%, users reporting failures

**Response:**
1. Check external API status
2. Review error logs for patterns
3. Check resource usage
4. Implement circuit breakers if API issue
5. Rollback if recent deployment
6. Scale resources if capacity issue

**Typical Resolution Time:** 15-30 minutes

### Scenario 3: Performance Degradation

**Symptoms:** Slow response times, timeouts

**Response:**
1. Check memory usage
2. Check database size
3. Check external API latency
4. Clean up temporary files
5. Restart service to clear memory
6. Scale resources if needed

**Typical Resolution Time:** 20-40 minutes

### Scenario 4: External Service Failure

**Symptoms:** Specific functionality failing (STT, TTS, memory)

**Response:**
1. Verify external service status
2. Check API keys and quotas
3. Implement circuit breaker
4. Enable fallback mode if available
5. Wait for service recovery
6. Communicate expected resolution time

**Typical Resolution Time:** Depends on external service

### Scenario 5: Database Issues

**Symptoms:** Session errors, memory failures, corruption

**Response:**
1. Check database file integrity
2. Check disk space
3. Restore from backup if corrupted
4. Run database maintenance (VACUUM)
5. Migrate to new database if needed
6. Verify data consistency

**Typical Resolution Time:** 30-60 minutes

## Incident Metrics and Review

### Track for Each Incident

- **Detection Time:** Time from issue start to detection
- **Response Time:** Time from detection to first action
- **Mitigation Time:** Time from first action to mitigation
- **Recovery Time:** Time from mitigation to full recovery
- **Total Duration:** Total incident time
- **User Impact:** Number of users/requests affected
- **Root Cause:** Category of root cause

### Monthly Review

- Total incidents by severity
- Average resolution time by severity
- Most common root causes
- Trends over time
- Effectiveness of improvements

### Continuous Improvement

- Update runbooks based on incidents
- Add monitoring for detected gaps
- Improve testing for root causes
- Train team on new procedures
- Automate common responses

## Post-Mortem Template

```markdown
# Incident Post-Mortem: [Brief Description]

**Date:** [Date]
**Severity:** SEV-[1/2/3/4]
**Duration:** [Total time]
**Incident Commander:** [Name]

## Summary

[2-3 sentence summary of what happened]

## Timeline

- [HH:MM] - Issue started
- [HH:MM] - Detected by [monitoring/user report]
- [HH:MM] - Incident declared
- [HH:MM] - Root cause identified
- [HH:MM] - Mitigation started
- [HH:MM] - Service recovered
- [HH:MM] - Incident closed

## Impact

- **Users Affected:** [Number/percentage]
- **Requests Failed:** [Number]
- **Revenue Impact:** [If applicable]
- **Data Loss:** [None/Description]

## Root Cause

[Detailed explanation of what caused the incident]

## What Went Well

- [Things that worked well in response]
- [Effective tools or procedures]
- [Good team coordination]

## What Went Wrong

- [Things that didn't work well]
- [Gaps in monitoring or alerting]
- [Unclear procedures]

## Action Items

- [ ] [Immediate fix] - Owner: [Name] - Due: [Date]
- [ ] [Add monitoring] - Owner: [Name] - Due: [Date]
- [ ] [Improve testing] - Owner: [Name] - Due: [Date]
- [ ] [Update documentation] - Owner: [Name] - Due: [Date]

## Lessons Learned

[Key takeaways and improvements for future incidents]
```

## Related Documentation

- [Operations Runbook](OPERATIONS_RUNBOOK.md)
- [Rollback Procedures](ROLLBACK_PROCEDURES.md)
- [Deployment Checklist](DEPLOYMENT_CHECKLIST.md)
- [Monitoring and Observability](MONITORING_AND_OBSERVABILITY.md)

---

**Last Updated:** October 21, 2025  
**Next Review:** January 21, 2026  
**Owner:** Engineering Team
