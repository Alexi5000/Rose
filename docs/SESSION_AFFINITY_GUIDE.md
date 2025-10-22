# Session Affinity Configuration Guide

## Overview

Session affinity (also called "sticky sessions") routes requests from the same user to the same application instance. This guide explains when to use session affinity, how to configure it, and the trade-offs involved.

## What is Session Affinity?

```
Without Session Affinity:
User Request 1 → Load Balancer → Instance A
User Request 2 → Load Balancer → Instance B
User Request 3 → Load Balancer → Instance C

With Session Affinity:
User Request 1 → Load Balancer → Instance A
User Request 2 → Load Balancer → Instance A (same instance)
User Request 3 → Load Balancer → Instance A (same instance)
```

## When to Use Session Affinity

### ✅ Use Session Affinity If:

1. **In-Memory Caching**: Application caches data in memory per session
2. **WebSocket Connections**: Long-lived connections need to stay on same instance
3. **Stateful Operations**: Temporary state stored in application memory
4. **Performance Optimization**: Reducing database queries through local caching

### ❌ Don't Use Session Affinity If:

1. **Stateless Application**: All state in database (like Rose with PostgreSQL)
2. **High Availability Priority**: Want automatic failover to healthy instances
3. **Even Load Distribution**: Need perfect load balancing
4. **Simple Architecture**: Want to avoid complexity

## Rose Application Analysis

### Current Architecture

The Rose application is **mostly stateless** with PostgreSQL:
- ✅ Conversation state in PostgreSQL (shared across instances)
- ✅ Long-term memory in Qdrant (shared across instances)
- ✅ Session data in database (shared across instances)
- ⚠️ TTS cache in local filesystem (not shared)
- ⚠️ Temporary audio files in local filesystem (not shared)

### Recommendation

**Session affinity is OPTIONAL for Rose**:
- **Without affinity**: Works perfectly, slightly more database queries
- **With affinity**: Potential performance improvement, more complexity

**Start without session affinity**, add only if performance testing shows significant benefit.

## Configuration Options

### Option 1: Railway (Managed Platform)

Railway may not support session affinity directly. Check current documentation:

```json
// railway.json (check if supported)
{
  "deploy": {
    "sessionAffinity": "ip_hash"
  }
}
```

**Alternative**: Use Railway's built-in load balancing (no affinity)

### Option 2: Nginx (Self-Hosted)

If self-hosting with Nginx:

```nginx
# /etc/nginx/nginx.conf

upstream rose_backend {
    # IP hash: Route same IP to same instance
    ip_hash;
    
    server instance1.internal:8080;
    server instance2.internal:8080;
    server instance3.internal:8080;
}

server {
    listen 80;
    server_name rose.example.com;
    
    location / {
        proxy_pass http://rose_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**Pros**:
- Simple configuration
- No application changes needed
- Works with any backend

**Cons**:
- Users behind same NAT go to same instance (uneven distribution)
- No failover if instance goes down

### Option 3: AWS Application Load Balancer

If deploying on AWS:

```yaml
# CloudFormation template
Resources:
  TargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      TargetType: ip
      Protocol: HTTP
      Port: 8080
      VpcId: !Ref VPC
      HealthCheckPath: /api/health
      
      # Enable sticky sessions
      TargetGroupAttributes:
        - Key: stickiness.enabled
          Value: true
        - Key: stickiness.type
          Value: lb_cookie
        - Key: stickiness.lb_cookie.duration_seconds
          Value: 3600  # 1 hour
```

**Pros**:
- Cookie-based (more accurate than IP)
- Automatic failover to healthy instances
- Configurable duration

**Cons**:
- AWS-specific
- Requires cookie support in client

### Option 4: Cloudflare Load Balancer

If using Cloudflare:

```yaml
# Cloudflare Load Balancer config (via API or dashboard)
load_balancer:
  name: rose-lb
  default_pools:
    - rose-pool
  session_affinity: cookie
  session_affinity_ttl: 3600
  session_affinity_attributes:
    samesite: Lax
    secure: true
```

**Pros**:
- Global load balancing
- DDoS protection included
- Cookie-based affinity

**Cons**:
- Requires Cloudflare Pro plan ($20/month)
- Additional complexity

### Option 5: Application-Level Routing

Implement in application code:

```python
# src/ai_companion/interfaces/web/middleware/session_affinity.py
from fastapi import Request, Response
import hashlib

INSTANCE_ID = os.getenv("INSTANCE_ID", "instance-1")
TOTAL_INSTANCES = int(os.getenv("TOTAL_INSTANCES", "3"))

@app.middleware("http")
async def session_affinity_middleware(request: Request, call_next):
    # Get or create session ID
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Calculate target instance
    session_hash = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
    target_instance = session_hash % TOTAL_INSTANCES
    current_instance = int(INSTANCE_ID.split("-")[1]) - 1
    
    # If request should go to different instance, redirect
    if target_instance != current_instance:
        target_url = f"https://instance-{target_instance + 1}.rose.com{request.url.path}"
        return RedirectResponse(url=target_url)
    
    # Process request
    response = await call_next(request)
    
    # Set session cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=3600,
        httponly=True,
        samesite="lax"
    )
    
    return response
```

**Pros**:
- Full control
- Works with any infrastructure
- Can implement custom logic

**Cons**:
- Complex to implement
- Requires multiple domains or ports
- More code to maintain

## Implementation Steps

### Step 1: Enable Feature Flag

```bash
# .env or Railway variables
FEATURE_SESSION_AFFINITY_ENABLED=true
```

### Step 2: Configure Load Balancer

Choose one of the options above based on your infrastructure.

### Step 3: Test Session Affinity

```python
# scripts/test_session_affinity.py
import requests

def test_affinity():
    session = requests.Session()
    base_url = "https://your-app.railway.app"
    
    # Make multiple requests
    for i in range(10):
        response = session.get(f"{base_url}/api/health")
        instance_id = response.headers.get("X-Instance-ID", "unknown")
        print(f"Request {i+1}: Instance {instance_id}")
    
    # All requests should go to same instance

if __name__ == "__main__":
    test_affinity()
```

### Step 4: Add Instance ID Header

```python
# src/ai_companion/interfaces/web/app.py
import os

INSTANCE_ID = os.getenv("RAILWAY_REPLICA_ID", os.getenv("INSTANCE_ID", "unknown"))

@app.middleware("http")
async def add_instance_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Instance-ID"] = INSTANCE_ID
    return response
```

### Step 5: Monitor Distribution

```python
# scripts/monitor_load_distribution.py
import requests
from collections import Counter

def monitor_distribution(num_requests=100):
    base_url = "https://your-app.railway.app"
    instances = []
    
    for _ in range(num_requests):
        response = requests.get(f"{base_url}/api/health")
        instance_id = response.headers.get("X-Instance-ID", "unknown")
        instances.append(instance_id)
    
    # Count distribution
    distribution = Counter(instances)
    
    print("Load Distribution:")
    for instance, count in distribution.items():
        percentage = (count / num_requests) * 100
        print(f"  {instance}: {count} requests ({percentage:.1f}%)")
    
    # Check if evenly distributed
    expected = num_requests / len(distribution)
    variance = sum((count - expected) ** 2 for count in distribution.values()) / len(distribution)
    print(f"\nVariance: {variance:.2f} (lower is better)")

if __name__ == "__main__":
    monitor_distribution()
```

## Performance Impact

### Without Session Affinity

**Pros**:
- ✅ Perfect load distribution
- ✅ Automatic failover
- ✅ Simple architecture
- ✅ No cookie overhead

**Cons**:
- ⚠️ More database queries (no local cache hits)
- ⚠️ TTS cache misses (cache on different instance)
- ⚠️ Slightly higher latency (~10-50ms)

**Expected Performance**:
- Response time: 500-1000ms (voice processing)
- Database queries: 3-5 per request
- TTS cache hit rate: 0% (no shared cache)

### With Session Affinity

**Pros**:
- ✅ Local cache hits (TTS, session data)
- ✅ Fewer database queries
- ✅ Lower latency (~10-50ms improvement)

**Cons**:
- ⚠️ Uneven load distribution
- ⚠️ No automatic failover (session lost if instance dies)
- ⚠️ More complex architecture
- ⚠️ Cookie overhead

**Expected Performance**:
- Response time: 450-950ms (voice processing)
- Database queries: 2-4 per request
- TTS cache hit rate: 30-50% (if same phrases repeated)

### Benchmark Results (Estimated)

| Metric | Without Affinity | With Affinity | Improvement |
|--------|------------------|---------------|-------------|
| Response Time (p50) | 600ms | 550ms | 8% |
| Response Time (p95) | 1200ms | 1100ms | 8% |
| Database Queries | 4/request | 3/request | 25% |
| TTS Cache Hit Rate | 0% | 40% | +40% |
| Load Distribution | Perfect | Uneven | -20% |

**Conclusion**: Session affinity provides **marginal improvement** (~8% latency) at the cost of complexity.

## Monitoring

### Key Metrics

1. **Load Distribution**:
```sql
-- Count requests per instance (from logs)
SELECT instance_id, COUNT(*) as request_count
FROM request_logs
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY instance_id;
```

2. **Session Stickiness**:
```sql
-- Check if sessions stay on same instance
SELECT session_id, COUNT(DISTINCT instance_id) as instance_count
FROM request_logs
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY session_id
HAVING COUNT(DISTINCT instance_id) > 1;
```

3. **Cache Hit Rate**:
```python
# In application metrics
tts_cache_hits = metrics.get("tts.cache.hits")
tts_cache_misses = metrics.get("tts.cache.misses")
hit_rate = tts_cache_hits / (tts_cache_hits + tts_cache_misses)
```

### Alerts

Set up alerts for:
- Uneven load distribution (>30% variance)
- Session stickiness failures (>5%)
- Instance failures (no requests for 5 minutes)

## Troubleshooting

### Issue: Uneven Load Distribution

**Symptoms**:
- One instance gets 80% of traffic
- Other instances idle

**Causes**:
- IP hash with users behind same NAT
- Cookie not being set correctly
- Load balancer misconfiguration

**Solutions**:
1. Switch to cookie-based affinity (not IP-based)
2. Verify cookies are being set and sent
3. Check load balancer logs
4. Consider disabling affinity

### Issue: Session Lost on Instance Failure

**Symptoms**:
- User loses conversation when instance restarts
- "Session not found" errors

**Causes**:
- Session affinity without failover
- Local state not in database

**Solutions**:
1. Ensure all state is in PostgreSQL (not local memory)
2. Configure load balancer failover
3. Implement session recovery logic
4. Consider disabling affinity

### Issue: Cookie Not Persisting

**Symptoms**:
- Requests go to different instances
- Session affinity not working

**Causes**:
- Cookie settings incorrect (SameSite, Secure)
- Browser blocking cookies
- CORS issues

**Solutions**:
1. Check cookie settings:
```python
response.set_cookie(
    key="session_id",
    value=session_id,
    max_age=3600,
    httponly=True,
    secure=True,  # HTTPS only
    samesite="lax"  # or "none" for cross-site
)
```
2. Verify CORS allows credentials
3. Test in different browsers

## Decision Matrix

| Scenario | Recommendation | Reason |
|----------|----------------|--------|
| Single instance | No affinity | Not needed |
| 2-3 instances, PostgreSQL | No affinity | Minimal benefit, added complexity |
| 5+ instances, high traffic | Consider affinity | May improve performance |
| WebSocket connections | Yes, affinity | Required for connection persistence |
| Stateless API | No affinity | No benefit |
| In-memory caching | Yes, affinity | Improves cache hit rate |

## Recommendation for Rose

**Start without session affinity**:
1. Deploy 2-3 instances with PostgreSQL
2. Monitor performance for 1-2 weeks
3. Measure response times and database load
4. If performance is acceptable, keep it simple
5. If performance is poor, consider adding affinity

**Add session affinity only if**:
- Response time p95 > 2 seconds
- Database connection pool exhausted
- TTS cache hit rate matters (repeated phrases)
- Performance testing shows >15% improvement

## References

- [AWS ALB Sticky Sessions](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/sticky-sessions.html)
- [Nginx Load Balancing](https://nginx.org/en/docs/http/load_balancing.html)
- [Cloudflare Load Balancing](https://developers.cloudflare.com/load-balancing/)
- [Railway Load Balancing](https://docs.railway.app/) (check for updates)

## Conclusion

Session affinity is a **performance optimization**, not a requirement. The Rose application works perfectly without it thanks to PostgreSQL shared state. Consider adding it only after measuring actual performance bottlenecks in production.

**Recommended Approach**:
1. ✅ Deploy with PostgreSQL (no affinity)
2. ✅ Monitor performance
3. ✅ Optimize database queries first
4. ✅ Add affinity only if needed
5. ✅ Keep architecture simple
