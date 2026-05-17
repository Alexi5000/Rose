# Resource Management

This document describes the resource management optimizations implemented in the Rose application to ensure efficient operation and prevent resource exhaustion in production environments.

## Overview

The application implements several resource management strategies:

1. **Qdrant Connection Pooling** - Singleton pattern for efficient database connections
2. **Session Cleanup** - Automatic removal of old session data
3. **Request Size Limits** - Protection against memory exhaustion from large payloads
4. **Static File Caching** - Optimized frontend asset delivery

## 1. Qdrant Connection Pooling

### Implementation

The `VectorStore` class implements a singleton pattern to ensure only one Qdrant client instance is created and reused across all requests. This provides:

- **Connection pooling**: Qdrant client maintains an internal connection pool
- **Resource efficiency**: No redundant client instantiation
- **Thread safety**: Single instance shared across all requests

### Location

- `src/ai_companion/modules/memory/long_term/vector_store.py`

### Usage

```python
from ai_companion.modules.memory.long_term.vector_store import get_vector_store

# Always returns the same instance
vector_store = get_vector_store()
```

### Benefits

- Reduced memory footprint
- Faster request processing (no client initialization overhead)
- Efficient connection management to Qdrant Cloud

## 2. Session Cleanup

### Implementation

Automatic cleanup of old session data from the SQLite checkpointer database to prevent unbounded growth.

### Configuration

```bash
# .env
SESSION_RETENTION_DAYS=7  # Delete sessions older than 7 days
```

### Schedule

- **Frequency**: Daily at 3:00 AM
- **Retention**: Configurable via `SESSION_RETENTION_DAYS` (default: 7 days)
- **Method**: Conservative approach - only deletes verified old sessions

### Location

- `src/ai_companion/core/session_cleanup.py`
- Scheduled in `src/ai_companion/interfaces/web/app.py` lifespan

### Monitoring

The cleanup job logs structured information:

```json
{
  "event": "session_cleanup_analysis",
  "total_sessions": 150,
  "total_checkpoints": 3000,
  "retention_days": 7,
  "cutoff_date": "2025-10-13T00:00:00"
}
```

### Manual Execution

```python
from ai_companion.core.session_cleanup import cleanup_old_sessions

# Clean up sessions older than 7 days
stats = cleanup_old_sessions(retention_days=7)
print(stats)  # {'sessions_deleted': 0, 'checkpoints_deleted': 0, 'errors': []}
```

### Safety Features

- **Conservative approach**: Only deletes sessions with verified age
- **Error handling**: Graceful failure with detailed logging
- **Database safety**: Uses transactions and proper connection management
- **Dry-run capable**: Returns statistics without deletion

## 3. Request Size Limits

### Implementation

Middleware-based request size validation to prevent memory exhaustion from large payloads.

### Configuration

```bash
# .env
MAX_REQUEST_SIZE=10485760  # 10MB in bytes
```

### Behavior

- **Applies to**: POST, PUT, PATCH requests
- **Check**: Content-Length header validation
- **Response**: 413 Payload Too Large with descriptive error

### Error Response

```json
{
  "error": "request_too_large",
  "message": "Request body too large. Maximum size is 10.0MB",
  "max_size_bytes": 10485760
}
```

### Location

- Middleware in `src/ai_companion/interfaces/web/app.py`
- Configuration in `src/ai_companion/settings.py`

### Benefits

- Prevents memory exhaustion
- Early rejection of oversized requests
- Clear error messages for clients

## 4. Static File Caching

### Implementation

HTTP cache headers for optimized frontend asset delivery.

### Cache Strategy

| Resource Type | Cache-Control | Duration | Rationale |
|--------------|---------------|----------|-----------|
| Static assets (`/static/*`) | `public, max-age=31536000, immutable` | 1 year | Immutable files with content hashing |
| API responses (`/api/*`) | `no-cache, no-store, must-revalidate` | None | Always fresh data |
| HTML files (`/`, `*.html`) | `public, max-age=300` | 5 minutes | Allow quick updates |

### Location

- Middleware in `src/ai_companion/interfaces/web/app.py`

### Benefits

- **Reduced bandwidth**: Cached assets not re-downloaded
- **Faster page loads**: Browser serves from cache
- **Lower server load**: Fewer requests for static files
- **CDN-friendly**: Long cache times work well with CDNs

### Example Headers

```http
# Static asset (JS/CSS)
Cache-Control: public, max-age=31536000, immutable

# API response
Cache-Control: no-cache, no-store, must-revalidate

# HTML page
Cache-Control: public, max-age=300
```

## Background Jobs

The application runs several scheduled background jobs for resource management:

### Job Schedule

| Job | Schedule | Purpose | Configuration |
|-----|----------|---------|---------------|
| Audio Cleanup | Every hour | Delete audio files older than 24 hours | N/A |
| Database Backup | Daily at 2:00 AM | Backup SQLite database | Keep 7 days |
| Session Cleanup | Daily at 3:00 AM | Delete old sessions | `SESSION_RETENTION_DAYS` |

### Monitoring Jobs

All jobs log structured events:

```json
{
  "event": "scheduler_started",
  "jobs": ["audio_cleanup", "database_backup", "session_cleanup"]
}
```

### Job Management

Jobs are managed by APScheduler and run in the FastAPI lifespan context:

```python
# Jobs start automatically with the application
# Jobs stop automatically on shutdown
# Jobs are idempotent and safe to run multiple times
```

## Performance Considerations

### Memory Usage

- **Qdrant singleton**: ~50MB per instance (vs ~50MB × N requests)
- **Request size limit**: Prevents >10MB payloads from loading into memory
- **Session cleanup**: Prevents unbounded SQLite database growth

### Disk Usage

- **Audio cleanup**: Prevents `/tmp` directory exhaustion
- **Session cleanup**: Keeps SQLite database size manageable
- **Database backups**: Automatic rotation prevents backup accumulation

### Network Usage

- **Static file caching**: Reduces bandwidth by ~80% for repeat visitors
- **Qdrant connection pooling**: Reduces connection overhead

## Monitoring and Alerts

### Key Metrics to Monitor

1. **Memory usage**: Should stay within Railway limits (512MB-8GB)
2. **Disk usage**: Monitor `/app/data` volume size
3. **Session count**: Track growth rate and cleanup effectiveness
4. **Request rejection rate**: Monitor 413 errors for size limit tuning

### Recommended Alerts

```yaml
# Example alert thresholds
memory_usage: > 80% of limit
disk_usage: > 90% of volume
session_count: > 10,000 active sessions
request_rejection_rate: > 5% of requests
```

## Troubleshooting

### High Memory Usage

1. Check Qdrant singleton is working: `grep "VectorStore" logs`
2. Verify request size limits are enforced: `grep "request_too_large" logs`
3. Check for memory leaks in workflow execution

### Disk Space Issues

1. Verify audio cleanup is running: `grep "audio_cleanup" logs`
2. Check session cleanup effectiveness: `grep "session_cleanup" logs`
3. Monitor database backup rotation

### Slow Performance

1. Verify static file caching is working: Check `Cache-Control` headers
2. Check Qdrant connection pooling: Should see single client initialization
3. Monitor request size distribution: Large requests may need optimization

## Configuration Reference

### Environment Variables

```bash
# Resource Management
MAX_REQUEST_SIZE=10485760          # 10MB request size limit
SESSION_RETENTION_DAYS=7           # Session retention period

# Related Settings
WORKFLOW_TIMEOUT_SECONDS=60        # Prevent hanging requests
RATE_LIMIT_PER_MINUTE=10          # Prevent API abuse
```

### Defaults

All resource management features have sensible defaults and can be used without configuration:

- Request size limit: 10MB
- Session retention: 7 days
- Audio cleanup: 24 hours
- Database backups: 7 days

## Best Practices

1. **Monitor resource usage**: Track memory, disk, and network metrics
2. **Tune retention periods**: Adjust based on usage patterns
3. **Review logs regularly**: Check cleanup job effectiveness
4. **Test limits**: Verify request size limits match use cases
5. **Cache validation**: Ensure cache headers work with CDN/proxy

## Future Enhancements

Potential improvements for horizontal scaling:

1. **PostgreSQL migration**: Replace SQLite for multi-instance support
2. **Redis caching**: Add distributed caching layer
3. **S3 audio storage**: Move audio files to object storage
4. **Connection pooling**: Add explicit connection pool configuration
5. **Rate limiting**: Implement distributed rate limiting with Redis

## References

- [FastAPI Performance](https://fastapi.tiangolo.com/deployment/concepts/)
- [Qdrant Client Documentation](https://qdrant.tech/documentation/quick-start/)
- [HTTP Caching Best Practices](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
