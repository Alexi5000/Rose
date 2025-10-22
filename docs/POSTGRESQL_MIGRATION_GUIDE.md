# PostgreSQL Migration Guide

## Overview

This guide provides step-by-step instructions for migrating the Rose the Healer Shaman application from SQLite to PostgreSQL. This migration is necessary for horizontal scaling (running multiple instances) and improved reliability.

## Why Migrate?

### SQLite Limitations
- ❌ Single writer at a time (locks entire database)
- ❌ Cannot share state across multiple instances
- ❌ Limited concurrent access
- ❌ No built-in replication or high availability

### PostgreSQL Benefits
- ✅ Multiple concurrent writers (MVCC, row-level locking)
- ✅ Shared state across multiple instances
- ✅ Excellent concurrent access
- ✅ Built-in replication and backup tools
- ✅ Managed services available (Railway, AWS RDS, etc.)

## Prerequisites

### 1. Install PostgreSQL Dependencies

```bash
# Add to pyproject.toml
uv add "langgraph[postgres]" "psycopg[binary]"

# Or install directly
uv pip install "langgraph[postgres]" "psycopg[binary]"
```

### 2. Provision PostgreSQL Database

#### Option A: Railway (Recommended)

1. Go to Railway dashboard: https://railway.app
2. Click "New" → "Database" → "PostgreSQL"
3. Wait for provisioning (1-2 minutes)
4. Copy the connection string from "Connect" tab

```
postgresql://postgres:password@region.railway.app:5432/railway
```

#### Option B: Local PostgreSQL (Development)

```bash
# Install PostgreSQL
# macOS
brew install postgresql@15
brew services start postgresql@15

# Ubuntu/Debian
sudo apt-get install postgresql-15
sudo systemctl start postgresql

# Create database
createdb rose_dev

# Connection string
postgresql://localhost:5432/rose_dev
```

#### Option C: Other Managed Services

- **Render**: https://render.com/docs/databases
- **Supabase**: https://supabase.com (includes PostgreSQL)
- **AWS RDS**: https://aws.amazon.com/rds/postgresql/
- **Google Cloud SQL**: https://cloud.google.com/sql/postgresql

## Migration Steps

### Step 1: Update Environment Configuration

Add PostgreSQL configuration to your `.env` file:

```bash
# Database Configuration
FEATURE_DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:password@host:5432/database

# Optional: Connection pool settings
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

**Important**: Keep your SQLite configuration as backup:
```bash
# Backup SQLite path (for rollback)
SHORT_TERM_MEMORY_DB_PATH=/app/data/memory.db
```

### Step 2: Test Database Connection

Create a test script to verify connectivity:

```python
# scripts/test_postgres_connection.py
import psycopg
from ai_companion.settings import settings

def test_connection():
    try:
        conn = psycopg.connect(settings.DATABASE_URL)
        print("✅ PostgreSQL connection successful")
        
        # Test query
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print(f"PostgreSQL version: {version[0]}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
```

Run the test:
```bash
uv run python scripts/test_postgres_connection.py
```

### Step 3: Update Application Code

The application now uses the checkpointer factory, so no code changes are needed in most cases. However, verify the following files are using the factory:

#### Update Chainlit Interface

```python
# src/ai_companion/interfaces/chainlit/app.py
from ai_companion.core.checkpointer import get_async_checkpointer

# Replace AsyncSqliteSaver with factory
async with get_async_checkpointer() as checkpointer:
    graph = graph_builder.compile(checkpointer=checkpointer)
    # ... rest of code
```

#### Update Voice API

```python
# src/ai_companion/interfaces/web/routes/voice.py
from ai_companion.core.checkpointer import get_checkpointer

# Replace SqliteSaver with factory
checkpointer = get_checkpointer()
graph = create_workflow_graph().compile(checkpointer=checkpointer)
# ... rest of code
```

#### Update WhatsApp Interface

```python
# src/ai_companion/interfaces/whatsapp/whatsapp_response.py
from ai_companion.core.checkpointer import get_async_checkpointer

# Replace AsyncSqliteSaver with factory
async with get_async_checkpointer() as checkpointer:
    graph = graph_builder.compile(checkpointer=checkpointer)
    # ... rest of code
```

### Step 4: Initialize Database Schema

LangGraph automatically creates the required tables on first use. To verify:

```python
# scripts/init_postgres_schema.py
from ai_companion.core.checkpointer import get_checkpointer
from ai_companion.graph.graph import create_workflow_graph

def init_schema():
    print("Initializing PostgreSQL schema...")
    
    # Create checkpointer (this creates tables)
    checkpointer = get_checkpointer()
    
    # Compile graph (this verifies schema)
    graph = create_workflow_graph().compile(checkpointer=checkpointer)
    
    print("✅ Schema initialized successfully")

if __name__ == "__main__":
    init_schema()
```

Run the initialization:
```bash
uv run python scripts/init_postgres_schema.py
```

### Step 5: Test in Development

1. **Start the application**:
```bash
# Chainlit interface
uv run chainlit run src/ai_companion/interfaces/chainlit/app.py

# Or voice API
uv run fastapi dev src/ai_companion/interfaces/web/app.py
```

2. **Create a test session**:
- Open the interface
- Start a conversation
- Send a few messages

3. **Verify data persistence**:
```sql
-- Connect to PostgreSQL
psql $DATABASE_URL

-- Check tables
\dt

-- Check checkpoints
SELECT * FROM checkpoints LIMIT 5;

-- Check writes
SELECT * FROM checkpoint_writes LIMIT 5;
```

4. **Test session recovery**:
- Restart the application
- Resume the same session
- Verify conversation history is preserved

### Step 6: Migrate Existing Data (Optional)

If you want to preserve existing SQLite sessions:

```python
# scripts/migrate_sqlite_to_postgres.py
import sqlite3
import psycopg
from ai_companion.settings import settings

def migrate_data():
    # Connect to both databases
    sqlite_conn = sqlite3.connect(settings.SHORT_TERM_MEMORY_DB_PATH)
    pg_conn = psycopg.connect(settings.DATABASE_URL)
    
    try:
        # Get SQLite data
        sqlite_cur = sqlite_conn.cursor()
        sqlite_cur.execute("SELECT * FROM checkpoints")
        checkpoints = sqlite_cur.fetchall()
        
        # Insert into PostgreSQL
        pg_cur = pg_conn.cursor()
        for checkpoint in checkpoints:
            # Adjust column mapping based on LangGraph schema
            pg_cur.execute(
                "INSERT INTO checkpoints VALUES (%s, %s, %s, %s, %s)",
                checkpoint
            )
        
        pg_conn.commit()
        print(f"✅ Migrated {len(checkpoints)} checkpoints")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        pg_conn.rollback()
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate_data()
```

**Note**: This is a simplified example. The actual schema may differ. Inspect both databases first.

### Step 7: Deploy to Staging

1. **Update staging environment variables**:
```bash
# Railway CLI
railway variables set FEATURE_DATABASE_TYPE=postgresql
railway variables set DATABASE_URL=postgresql://...

# Or use Railway dashboard
```

2. **Deploy**:
```bash
railway up
```

3. **Run smoke tests**:
```bash
# Test health endpoint
curl https://your-staging-app.railway.app/api/health

# Test session creation
curl -X POST https://your-staging-app.railway.app/api/session/start
```

4. **Monitor logs**:
```bash
railway logs --tail
```

### Step 8: Performance Testing

Run load tests to verify PostgreSQL performance:

```bash
# Using Locust
uv run locust -f tests/locustfile.py --host=https://your-staging-app.railway.app

# Or using Apache Bench
ab -n 1000 -c 10 https://your-staging-app.railway.app/api/health
```

**Expected Results**:
- Response time: <100ms for health checks
- Response time: <2s for voice processing
- No database connection errors
- No timeout errors

### Step 9: Deploy to Production

1. **Backup SQLite data** (if needed):
```bash
# Download current SQLite database
railway run cp /app/data/memory.db /tmp/memory_backup.db
railway run cat /tmp/memory_backup.db > memory_backup.db
```

2. **Update production environment**:
```bash
railway variables set FEATURE_DATABASE_TYPE=postgresql --environment production
railway variables set DATABASE_URL=postgresql://... --environment production
```

3. **Deploy**:
```bash
railway up --environment production
```

4. **Monitor closely**:
- Watch error rates
- Check response times
- Verify session creation
- Monitor database connections

### Step 10: Verify and Monitor

1. **Check application logs**:
```bash
railway logs --environment production | grep -i postgres
```

Expected log entries:
```
INFO: Using PostgreSQL checkpointer database_url=region.railway.app:5432
```

2. **Monitor database metrics**:
- Connection count
- Query latency
- Active sessions
- Database size

3. **Test session persistence**:
- Create a session
- Restart the application
- Verify session is preserved

## Rollback Procedure

If issues occur, you can quickly rollback to SQLite:

### Quick Rollback (No Data Loss)

1. **Change environment variable**:
```bash
railway variables set FEATURE_DATABASE_TYPE=sqlite
```

2. **Restart application**:
```bash
railway up --detach
```

3. **Verify**:
```bash
railway logs | grep -i sqlite
```

Expected:
```
INFO: Using SQLite checkpointer db_path=/app/data/memory.db
```

### Full Rollback (With Code Revert)

If the checkpointer factory has issues:

1. **Revert code changes**:
```bash
git revert <migration-commit-hash>
git push
```

2. **Railway will auto-deploy** the reverted code

3. **Update environment**:
```bash
railway variables set FEATURE_DATABASE_TYPE=sqlite
```

## Troubleshooting

### Issue: Connection Refused

**Symptoms**:
```
psycopg.OperationalError: connection to server failed: Connection refused
```

**Solutions**:
1. Verify DATABASE_URL is correct
2. Check database is running (Railway dashboard)
3. Verify network connectivity
4. Check firewall rules

### Issue: Authentication Failed

**Symptoms**:
```
psycopg.OperationalError: FATAL: password authentication failed
```

**Solutions**:
1. Verify username and password in DATABASE_URL
2. Check for special characters (URL encode if needed)
3. Regenerate database credentials (Railway dashboard)

### Issue: Too Many Connections

**Symptoms**:
```
psycopg.OperationalError: FATAL: too many connections
```

**Solutions**:
1. Reduce DATABASE_POOL_SIZE (default: 10)
2. Reduce DATABASE_MAX_OVERFLOW (default: 20)
3. Upgrade database plan (more connections)
4. Implement connection pooling with PgBouncer

### Issue: Slow Queries

**Symptoms**:
- Response times >2s
- Timeout errors

**Solutions**:
1. Check database region (should match app region)
2. Add indexes (LangGraph should handle this)
3. Upgrade database plan (more resources)
4. Enable query logging to identify slow queries

### Issue: Schema Mismatch

**Symptoms**:
```
psycopg.errors.UndefinedColumn: column "..." does not exist
```

**Solutions**:
1. Drop and recreate tables (development only!)
2. Verify LangGraph version matches
3. Check for manual schema modifications

## Performance Optimization

### 1. Connection Pooling

```python
# settings.py
DATABASE_POOL_SIZE=20  # Increase for high traffic
DATABASE_MAX_OVERFLOW=40
```

### 2. Read Replicas (Future)

```python
# settings.py
FEATURE_READ_REPLICA_ENABLED=true
DATABASE_READ_REPLICA_URL=postgresql://replica-host:5432/db

# Use replica for read-only queries
from ai_companion.core.checkpointer import get_checkpointer

# Write operations
write_checkpointer = get_checkpointer()

# Read operations (if implemented)
read_checkpointer = get_checkpointer(read_only=True)
```

### 3. Database Indexes

LangGraph creates indexes automatically, but you can verify:

```sql
-- Check indexes
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename IN ('checkpoints', 'checkpoint_writes');

-- Add custom index if needed (example)
CREATE INDEX idx_checkpoints_thread_id 
ON checkpoints(thread_id);
```

### 4. Monitoring Queries

```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Slow queries
SELECT pid, now() - query_start as duration, query 
FROM pg_stat_activity 
WHERE state = 'active' 
ORDER BY duration DESC;

-- Database size
SELECT pg_size_pretty(pg_database_size('railway'));
```

## Cost Estimation

### Railway PostgreSQL Pricing

| Plan | Storage | RAM | Connections | Price |
|------|---------|-----|-------------|-------|
| Starter | 1GB | 1GB | 22 | $5/month |
| Pro | 10GB | 2GB | 97 | $10/month |
| Custom | Custom | Custom | Custom | Variable |

### Recommendations

- **Development**: Starter plan ($5/month)
- **Staging**: Starter plan ($5/month)
- **Production (small)**: Pro plan ($10/month)
- **Production (large)**: Custom plan

## Next Steps

After successful migration:

1. ✅ **Enable Multiple Instances**: Deploy 2-3 instances behind load balancer
2. ✅ **Set Up Monitoring**: Track database metrics and query performance
3. ✅ **Configure Backups**: Enable automated backups (Railway does this automatically)
4. ✅ **Test Failover**: Verify application handles database restarts
5. ✅ **Document**: Update deployment documentation with PostgreSQL setup

## References

- [LangGraph PostgreSQL Checkpointer](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.postgres.PostgresSaver)
- [Railway PostgreSQL Docs](https://docs.railway.app/databases/postgresql)
- [psycopg3 Documentation](https://www.psycopg.org/psycopg3/docs/)
- [PostgreSQL Connection Pooling](https://www.postgresql.org/docs/current/runtime-config-connection.html)

## Support

If you encounter issues during migration:

1. Check logs: `railway logs --tail`
2. Review this guide's troubleshooting section
3. Check Railway status: https://status.railway.app
4. Contact Railway support: https://railway.app/help
