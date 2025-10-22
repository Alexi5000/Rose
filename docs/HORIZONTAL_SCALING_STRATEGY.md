# Horizontal Scaling Strategy

## Overview

This document outlines the strategy for scaling the Rose the Healer Shaman application horizontally to support multiple instances and higher user loads. The current architecture uses SQLite for conversation state persistence, which limits the application to a single instance. This document evaluates migration options and provides a roadmap for horizontal scaling.

## Current Architecture Limitations

### Single Instance Constraint

The application currently uses SQLite (`SqliteSaver`) for LangGraph checkpointer state:
- **Location**: `SHORT_TERM_MEMORY_DB_PATH` (default: `/app/data/memory.db`)
- **Usage**: Conversation state, workflow checkpoints
- **Limitation**: SQLite does not support concurrent writes from multiple processes/instances

### Impact on Scaling

- Cannot deploy multiple instances behind a load balancer
- Single point of failure (no redundancy)
- Limited to vertical scaling only (increasing resources of single instance)
- Maximum capacity: ~50-100 concurrent users per instance

## PostgreSQL Migration Evaluation

### Benefits of PostgreSQL

1. **Multi-Instance Support**: Supports concurrent connections from multiple application instances
2. **ACID Compliance**: Strong consistency guarantees for conversation state
3. **Scalability**: Can handle thousands of concurrent connections
4. **Managed Services**: Available on Railway, Render, AWS RDS, Google Cloud SQL
5. **Backup & Recovery**: Built-in replication and point-in-time recovery
6. **Connection Pooling**: Efficient resource management with PgBouncer

### LangGraph PostgreSQL Support

LangGraph provides native PostgreSQL checkpointer support:

```python
from langgraph.checkpoint.postgres import PostgresSaver

# Synchronous version
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:password@host:port/database"
)

# Asynchronous version
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async with AsyncPostgresSaver.from_conn_string(
    "postgresql://user:password@host:port/database"
) as checkpointer:
    graph = graph_builder.compile(checkpointer=checkpointer)
```

### Migration Complexity

**Low to Medium Complexity**:
- ✅ LangGraph provides drop-in replacement (`PostgresSaver` vs `SqliteSaver`)
- ✅ Same API interface, minimal code changes required
- ✅ Automatic schema creation by LangGraph
- ⚠️ Requires PostgreSQL database provisioning
- ⚠️ Need to migrate existing session data (if preserving history)
- ⚠️ Connection string management and pooling configuration

### Cost Considerations

**Railway PostgreSQL Pricing** (as of 2024):
- Starter: $5/month (1GB storage, 1GB RAM)
- Pro: $10/month (10GB storage, 2GB RAM)
- Additional: $0.25/GB storage, $10/GB RAM

**Comparison to SQLite**:
- SQLite: Free (uses application storage)
- PostgreSQL: $5-10/month minimum
- **Recommendation**: Worth the cost for production deployments requiring redundancy

### Performance Considerations

**SQLite Performance**:
- Read: Very fast (local file access)
- Write: Fast for single writer
- Concurrent: Limited (locks entire database)

**PostgreSQL Performance**:
- Read: Fast with proper indexing
- Write: Good with connection pooling
- Concurrent: Excellent (MVCC, row-level locking)
- Network latency: 1-5ms (same region)

**Expected Impact**:
- Slight increase in latency (1-5ms per checkpoint operation)
- Much better throughput under concurrent load
- No blocking between instances

## Migration Implementation Plan

### Phase 1: Add PostgreSQL Support (Backward Compatible)

1. **Add PostgreSQL dependency**:
   ```toml
   # pyproject.toml
   dependencies = [
       "langgraph[postgres]>=0.2.0",
       "psycopg[binary]>=3.1.0",
   ]
   ```

2. **Add database configuration**:
   ```python
   # settings.py
   DATABASE_TYPE: str = "sqlite"  # "sqlite" or "postgresql"
   DATABASE_URL: str | None = None  # PostgreSQL connection string
   DATABASE_POOL_SIZE: int = 10
   DATABASE_MAX_OVERFLOW: int = 20
   ```

3. **Create checkpointer factory**:
   ```python
   # src/ai_companion/core/checkpointer.py
   def get_checkpointer():
       if settings.DATABASE_TYPE == "postgresql":
           return PostgresSaver.from_conn_string(settings.DATABASE_URL)
       else:
           return SqliteSaver.from_conn_string(settings.SHORT_TERM_MEMORY_DB_PATH)
   ```

4. **Update all interfaces** to use factory instead of direct SQLite imports

### Phase 2: Test PostgreSQL in Staging

1. Provision PostgreSQL database on Railway
2. Configure `DATABASE_TYPE=postgresql` and `DATABASE_URL`
3. Run full test suite against PostgreSQL
4. Performance testing with concurrent requests
5. Verify session persistence across restarts

### Phase 3: Data Migration (Optional)

If preserving existing sessions:

```python
# scripts/migrate_sqlite_to_postgres.py
import sqlite3
import psycopg

def migrate_sessions():
    # Read from SQLite
    sqlite_conn = sqlite3.connect(settings.SHORT_TERM_MEMORY_DB_PATH)
    
    # Write to PostgreSQL
    pg_conn = psycopg.connect(settings.DATABASE_URL)
    
    # Copy checkpoint data
    # (Implementation depends on LangGraph schema)
```

### Phase 4: Production Deployment

1. Deploy with PostgreSQL in production
2. Monitor performance and error rates
3. Keep SQLite as fallback option (feature flag)
4. Gradually increase traffic to new setup

## Session Affinity Configuration

### Why Session Affinity?

Even with PostgreSQL, session affinity (sticky sessions) can improve performance by:
- Reducing database queries (in-memory caching)
- Maintaining WebSocket connections
- Reducing context switching

### Implementation Options

#### Option 1: Load Balancer Session Affinity

**Railway** (using Railway Proxy):
```json
// railway.json
{
  "deploy": {
    "sessionAffinity": "ip_hash"
  }
}
```
Note: Railway may not support this directly. Check documentation.

**Nginx** (if self-hosting):
```nginx
upstream rose_backend {
    ip_hash;  # Route same IP to same instance
    server instance1:8080;
    server instance2:8080;
    server instance3:8080;
}
```

**AWS ALB**:
```yaml
# Enable sticky sessions with cookie
TargetGroup:
  Stickiness:
    Enabled: true
    Type: lb_cookie
    DurationSeconds: 3600
```

#### Option 2: Client-Side Session Routing

Store instance ID in session and route accordingly:
```typescript
// Frontend
const sessionData = {
  sessionId: "uuid",
  instanceId: "instance-1"  // Returned by backend
}

// Route to specific instance
const apiUrl = `https://${instanceData.instanceId}.rose-api.com`
```

#### Option 3: No Session Affinity (Recommended)

With PostgreSQL, session affinity is **optional**:
- All instances share same database
- Session state is always consistent
- Simpler architecture, better fault tolerance
- Slight performance trade-off acceptable

**Recommendation**: Start without session affinity, add only if performance testing shows significant benefit.

## Multi-Region Deployment Strategy

### Current Single-Region Architecture

```
┌─────────────┐
│   Users     │
│  (Global)   │
└──────┬──────┘
       │
┌──────▼──────────────┐
│  Railway US-West    │
│  ┌──────────────┐   │
│  │ Rose App     │   │
│  │ Instance     │   │
│  └──────┬───────┘   │
│         │           │
│  ┌──────▼───────┐   │
│  │ PostgreSQL   │   │
│  └──────────────┘   │
└─────────────────────┘
```

### Multi-Region Architecture (Future)

```
┌─────────────┐
│   Users     │
│  (Global)   │
└──────┬──────┘
       │
┌──────▼──────────────────────────┐
│     Global Load Balancer        │
│     (Cloudflare / AWS)          │
└──┬─────────────────────────┬────┘
   │                         │
┌──▼──────────────┐   ┌──────▼─────────────┐
│  US-West        │   │  EU-Central        │
│  ┌───────────┐  │   │  ┌───────────┐     │
│  │ Rose App  │  │   │  │ Rose App  │     │
│  │ (3 inst)  │  │   │  │ (3 inst)  │     │
│  └─────┬─────┘  │   │  └─────┬─────┘     │
│        │        │   │        │           │
│  ┌─────▼─────┐  │   │  ┌─────▼─────┐     │
│  │PostgreSQL │  │   │  │PostgreSQL │     │
│  │ Primary   │◄─┼───┼─►│ Replica   │     │
│  └───────────┘  │   │  └───────────┘     │
└─────────────────┘   └────────────────────┘
```

### Multi-Region Considerations

#### 1. Database Replication

**Option A: Primary-Replica** (Recommended for MVP):
- Single primary database (US-West)
- Read replicas in other regions (EU, Asia)
- Writes go to primary (slight latency for non-US users)
- Reads from local replica (fast)

**Option B: Multi-Primary**:
- Multiple writable databases
- Conflict resolution required
- More complex, higher cost
- Only needed for very high scale

#### 2. Data Residency & Compliance

**GDPR Considerations**:
- EU user data should stay in EU
- Requires data partitioning by region
- Session routing based on user location

**Implementation**:
```python
# Route to region-specific database
def get_database_url(user_region: str) -> str:
    region_databases = {
        "us": os.getenv("DATABASE_URL_US"),
        "eu": os.getenv("DATABASE_URL_EU"),
        "asia": os.getenv("DATABASE_URL_ASIA"),
    }
    return region_databases.get(user_region, region_databases["us"])
```

#### 3. Qdrant Vector Database

**Current**: Single Qdrant Cloud cluster
**Multi-Region**: 
- Option A: Single cluster (acceptable latency for memory retrieval)
- Option B: Regional clusters with data sync
- **Recommendation**: Start with single cluster, monitor latency

#### 4. External API Latency

**Groq, ElevenLabs, Together AI**:
- APIs are typically multi-region
- Latency: 50-200ms regardless of app location
- **Impact**: Application region less critical than database region

### Multi-Region Deployment Phases

#### Phase 1: Single Region with Redundancy (Current Goal)
- Deploy 2-3 instances in US-West
- PostgreSQL with automated backups
- Load balancer with health checks
- **Capacity**: 200-500 concurrent users

#### Phase 2: Read Replicas
- Add PostgreSQL read replica in EU
- Route EU reads to replica
- All writes still to US primary
- **Capacity**: 500-1000 concurrent users

#### Phase 3: Full Multi-Region
- Deploy application instances in EU and Asia
- Regional databases with replication
- Global load balancer with geo-routing
- **Capacity**: 1000+ concurrent users

### Cost Estimation

**Single Region (Phase 1)**:
- Railway App (3 instances): $15-30/month
- PostgreSQL: $10/month
- **Total**: ~$25-40/month

**Multi-Region (Phase 3)**:
- Railway App (9 instances, 3 regions): $45-90/month
- PostgreSQL (3 databases): $30/month
- Global Load Balancer: $20/month
- **Total**: ~$95-140/month

## Feature Flags System

### Purpose

Feature flags enable:
- Gradual rollout of new features
- A/B testing
- Quick rollback without deployment
- Environment-specific features
- Database migration toggle (SQLite ↔ PostgreSQL)

### Implementation

See `docs/FEATURE_FLAGS.md` for detailed implementation.

Key flags for horizontal scaling:
- `database_type`: Toggle between SQLite and PostgreSQL
- `session_affinity_enabled`: Enable/disable sticky sessions
- `multi_region_enabled`: Enable regional routing
- `read_replica_enabled`: Use read replicas for queries

## Monitoring & Observability

### Key Metrics for Horizontal Scaling

1. **Instance Metrics**:
   - CPU usage per instance
   - Memory usage per instance
   - Request rate per instance
   - Active connections per instance

2. **Database Metrics**:
   - Connection pool utilization
   - Query latency (p50, p95, p99)
   - Active connections
   - Replication lag (if using replicas)

3. **Application Metrics**:
   - Session distribution across instances
   - Workflow execution time
   - External API latency
   - Error rate per instance

### Recommended Tools

- **Railway Metrics**: Built-in CPU, memory, network
- **PostgreSQL Monitoring**: pg_stat_statements, connection stats
- **Application Metrics**: Prometheus + Grafana (see `docs/MONITORING_AND_OBSERVABILITY.md`)
- **Distributed Tracing**: OpenTelemetry for request tracing across instances

## Rollout Plan

### Week 1-2: PostgreSQL Migration
- [ ] Add PostgreSQL support with feature flag
- [ ] Test in development environment
- [ ] Deploy to staging with PostgreSQL
- [ ] Run load tests (50-100 concurrent users)

### Week 3: Multi-Instance Deployment
- [ ] Deploy 2 instances in production
- [ ] Configure load balancer
- [ ] Monitor for 1 week
- [ ] Verify session consistency

### Week 4: Scale Testing
- [ ] Increase to 3 instances
- [ ] Load test with 200+ concurrent users
- [ ] Monitor database performance
- [ ] Optimize connection pooling

### Month 2-3: Optimization
- [ ] Add read replicas if needed
- [ ] Implement caching layer (Redis) if needed
- [ ] Optimize database queries
- [ ] Fine-tune instance resources

### Month 4+: Multi-Region (If Needed)
- [ ] Evaluate user distribution by region
- [ ] Deploy EU region if >20% EU traffic
- [ ] Set up database replication
- [ ] Configure geo-routing

## Decision Matrix

### When to Scale Horizontally?

| Metric | Threshold | Action |
|--------|-----------|--------|
| CPU Usage | >70% sustained | Add instance |
| Memory Usage | >80% sustained | Add instance or increase size |
| Response Time | p95 >2s | Add instance or optimize |
| Error Rate | >1% | Investigate before scaling |
| Concurrent Users | >80 per instance | Add instance |

### SQLite vs PostgreSQL Decision

**Use SQLite if**:
- Single instance deployment
- <50 concurrent users
- Development/staging environment
- Cost is primary concern

**Use PostgreSQL if**:
- Need multiple instances
- >50 concurrent users
- Production environment
- Need redundancy/backups
- Planning to scale

**Recommendation**: Migrate to PostgreSQL before deploying multiple instances.

## Risks & Mitigation

### Risk 1: Database Migration Failure
- **Mitigation**: Feature flag to rollback to SQLite
- **Testing**: Extensive staging testing before production
- **Backup**: Full SQLite backup before migration

### Risk 2: Increased Latency
- **Mitigation**: Connection pooling, read replicas
- **Monitoring**: Track p95/p99 latency
- **Optimization**: Database query optimization

### Risk 3: Cost Overrun
- **Mitigation**: Start with minimal setup (2 instances, small DB)
- **Monitoring**: Set up billing alerts
- **Scaling**: Scale gradually based on actual usage

### Risk 4: Session Inconsistency
- **Mitigation**: Comprehensive testing of concurrent access
- **Monitoring**: Track session-related errors
- **Fallback**: Session affinity as backup option

## Conclusion

The application is well-positioned for horizontal scaling with minimal changes:

1. **Immediate Action**: Migrate to PostgreSQL (1-2 weeks effort)
2. **Quick Win**: Deploy 2-3 instances behind load balancer
3. **Future-Proof**: Architecture supports multi-region expansion

**Estimated Capacity After Scaling**:
- Current (SQLite, 1 instance): 50-100 users
- Phase 1 (PostgreSQL, 3 instances): 200-500 users
- Phase 2 (Read replicas): 500-1000 users
- Phase 3 (Multi-region): 1000+ users

**Recommended Next Steps**:
1. Implement PostgreSQL checkpointer factory
2. Test in staging environment
3. Deploy 2 instances in production
4. Monitor and optimize
5. Scale based on actual usage patterns
