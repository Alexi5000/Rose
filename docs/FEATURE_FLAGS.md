# Feature Flags System

## Overview

This document describes the feature flags system for the Rose the Healer Shaman application. Feature flags enable gradual rollouts, A/B testing, quick rollbacks, and environment-specific feature control without requiring code deployments.

## Architecture

### Simple Environment-Based Flags (Current Implementation)

The application uses environment variables for feature flags, managed through `settings.py`:

```python
# settings.py
class Settings(BaseSettings):
    # Feature flags
    FEATURE_WHATSAPP_ENABLED: bool = False
    FEATURE_IMAGE_GENERATION_ENABLED: bool = False
    FEATURE_TTS_CACHE_ENABLED: bool = True
    FEATURE_DATABASE_TYPE: str = "sqlite"  # "sqlite" or "postgresql"
    FEATURE_SESSION_AFFINITY_ENABLED: bool = False
    FEATURE_READ_REPLICA_ENABLED: bool = False
    FEATURE_MULTI_REGION_ENABLED: bool = False
```

### Usage in Code

```python
from ai_companion.settings import settings

# Check feature flag
if settings.FEATURE_WHATSAPP_ENABLED:
    # WhatsApp integration code
    pass

# Database selection
if settings.FEATURE_DATABASE_TYPE == "postgresql":
    checkpointer = get_postgres_checkpointer()
else:
    checkpointer = get_sqlite_checkpointer()
```

## Available Feature Flags

### Core Features

#### `FEATURE_WHATSAPP_ENABLED`
- **Type**: Boolean
- **Default**: `false`
- **Purpose**: Enable WhatsApp integration
- **Status**: Frozen for future release
- **Dependencies**: Requires `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_TOKEN`, `WHATSAPP_VERIFY_TOKEN`

```bash
# Enable WhatsApp
FEATURE_WHATSAPP_ENABLED=true
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
WHATSAPP_TOKEN=your_token
WHATSAPP_VERIFY_TOKEN=your_verify_token
```

#### `FEATURE_IMAGE_GENERATION_ENABLED`
- **Type**: Boolean
- **Default**: `false`
- **Purpose**: Enable image generation via Together AI
- **Status**: Frozen for future release
- **Dependencies**: Requires `TOGETHER_API_KEY`

```bash
# Enable image generation
FEATURE_IMAGE_GENERATION_ENABLED=true
TOGETHER_API_KEY=your_api_key
```

#### `FEATURE_TTS_CACHE_ENABLED`
- **Type**: Boolean
- **Default**: `true`
- **Purpose**: Enable caching of TTS responses
- **Impact**: Reduces API calls and costs, improves response time
- **Trade-off**: Uses more disk space

```bash
# Disable TTS caching (not recommended)
FEATURE_TTS_CACHE_ENABLED=false
```

### Infrastructure Features

#### `FEATURE_DATABASE_TYPE`
- **Type**: String enum
- **Values**: `"sqlite"`, `"postgresql"`
- **Default**: `"sqlite"`
- **Purpose**: Select database backend for checkpointer
- **Use Case**: Horizontal scaling migration

```bash
# Use PostgreSQL for multi-instance deployment
FEATURE_DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

#### `FEATURE_SESSION_AFFINITY_ENABLED`
- **Type**: Boolean
- **Default**: `false`
- **Purpose**: Enable sticky sessions (route same user to same instance)
- **Use Case**: Performance optimization in multi-instance setup
- **Note**: Requires load balancer support

```bash
# Enable session affinity
FEATURE_SESSION_AFFINITY_ENABLED=true
```

#### `FEATURE_READ_REPLICA_ENABLED`
- **Type**: Boolean
- **Default**: `false`
- **Purpose**: Use read replicas for database queries
- **Use Case**: Multi-region deployment with read replicas
- **Dependencies**: Requires `DATABASE_READ_REPLICA_URL`

```bash
# Enable read replicas
FEATURE_READ_REPLICA_ENABLED=true
DATABASE_URL=postgresql://primary-host:5432/db
DATABASE_READ_REPLICA_URL=postgresql://replica-host:5432/db
```

#### `FEATURE_MULTI_REGION_ENABLED`
- **Type**: Boolean
- **Default**: `false`
- **Purpose**: Enable multi-region routing and data partitioning
- **Use Case**: Global deployment with regional databases
- **Dependencies**: Requires regional database URLs

```bash
# Enable multi-region
FEATURE_MULTI_REGION_ENABLED=true
DATABASE_URL_US=postgresql://us-host:5432/db
DATABASE_URL_EU=postgresql://eu-host:5432/db
DATABASE_URL_ASIA=postgresql://asia-host:5432/db
```

### Security & Performance Features

#### `RATE_LIMIT_ENABLED`
- **Type**: Boolean
- **Default**: `true`
- **Purpose**: Enable API rate limiting
- **Recommendation**: Always enabled in production

```bash
# Disable rate limiting (development only)
RATE_LIMIT_ENABLED=false
```

#### `ENABLE_SECURITY_HEADERS`
- **Type**: Boolean
- **Default**: `true`
- **Purpose**: Enable security headers (CSP, HSTS, etc.)
- **Recommendation**: Always enabled in production

```bash
# Disable security headers (development only)
ENABLE_SECURITY_HEADERS=false
```

#### `ENABLE_API_DOCS`
- **Type**: Boolean
- **Default**: `true`
- **Purpose**: Enable OpenAPI/Swagger documentation
- **Recommendation**: Enabled in dev/staging, optional in production

```bash
# Disable API docs in production
ENABLE_API_DOCS=false
```

## Implementation Guide

### Adding a New Feature Flag

1. **Add to Settings**:
```python
# src/ai_companion/settings.py
class Settings(BaseSettings):
    # Add new feature flag
    FEATURE_NEW_CAPABILITY_ENABLED: bool = False
```

2. **Update .env.example**:
```bash
# .env.example
# Feature Flags
FEATURE_NEW_CAPABILITY_ENABLED=false
```

3. **Use in Code**:
```python
# src/ai_companion/modules/new_capability.py
from ai_companion.settings import settings

def new_capability_function():
    if not settings.FEATURE_NEW_CAPABILITY_ENABLED:
        raise ValueError("New capability is not enabled")
    
    # Implementation
    pass
```

4. **Document**:
- Add to this document
- Update deployment documentation
- Add to API documentation if user-facing

### Feature Flag Best Practices

#### 1. Default to Safe State
```python
# Good: Default to disabled for new features
FEATURE_EXPERIMENTAL_AI: bool = False

# Good: Default to enabled for security features
ENABLE_SECURITY_HEADERS: bool = True
```

#### 2. Use Descriptive Names
```python
# Good
FEATURE_WHATSAPP_ENABLED: bool = False
FEATURE_DATABASE_TYPE: str = "sqlite"

# Bad
WHATSAPP: bool = False
DB: str = "sqlite"
```

#### 3. Validate Dependencies
```python
@field_validator("FEATURE_WHATSAPP_ENABLED")
@classmethod
def validate_whatsapp_config(cls, v: bool, info) -> bool:
    if v:  # If enabled, check required fields
        values = info.data
        if not values.get("WHATSAPP_TOKEN"):
            raise ValueError("WHATSAPP_TOKEN required when WhatsApp is enabled")
    return v
```

#### 4. Log Feature Flag State
```python
# At application startup
logger.info("Feature flags", extra={
    "whatsapp_enabled": settings.FEATURE_WHATSAPP_ENABLED,
    "database_type": settings.FEATURE_DATABASE_TYPE,
    "tts_cache_enabled": settings.FEATURE_TTS_CACHE_ENABLED,
})
```

## Environment-Specific Configuration

### Development
```bash
# .env (development)
FEATURE_WHATSAPP_ENABLED=false
FEATURE_IMAGE_GENERATION_ENABLED=true  # Test image generation
FEATURE_DATABASE_TYPE=sqlite
ENABLE_API_DOCS=true
RATE_LIMIT_ENABLED=false  # Easier testing
LOG_LEVEL=DEBUG
```

### Staging
```bash
# config/staging.env
FEATURE_WHATSAPP_ENABLED=false
FEATURE_IMAGE_GENERATION_ENABLED=false
FEATURE_DATABASE_TYPE=postgresql  # Test PostgreSQL
ENABLE_API_DOCS=true
RATE_LIMIT_ENABLED=true
LOG_LEVEL=INFO
```

### Production
```bash
# config/prod.env
FEATURE_WHATSAPP_ENABLED=false  # Not yet released
FEATURE_IMAGE_GENERATION_ENABLED=false  # Not yet released
FEATURE_DATABASE_TYPE=postgresql
ENABLE_API_DOCS=false  # Hide docs in production
RATE_LIMIT_ENABLED=true
ENABLE_SECURITY_HEADERS=true
LOG_LEVEL=INFO
```

## Gradual Rollout Strategy

### Phase 1: Development Testing
1. Enable feature in development environment
2. Test thoroughly with unit and integration tests
3. Verify no regressions

### Phase 2: Staging Deployment
1. Enable feature in staging environment
2. Run full test suite
3. Manual testing by team
4. Performance testing if applicable

### Phase 3: Canary Deployment (Optional)
1. Enable for 5% of production traffic
2. Monitor error rates and performance
3. Gradually increase to 25%, 50%, 100%

### Phase 4: Full Production Rollout
1. Enable for all production traffic
2. Monitor for 1-2 weeks
3. Remove feature flag code if stable

### Phase 5: Cleanup
1. Remove feature flag from code
2. Make feature always-on
3. Update documentation

## Rollback Procedures

### Immediate Rollback (No Deployment)

1. **Update Environment Variable**:
```bash
# Railway dashboard or CLI
railway variables set FEATURE_NEW_CAPABILITY_ENABLED=false
```

2. **Restart Application**:
```bash
railway up --detach
```

3. **Verify Rollback**:
```bash
# Check logs
railway logs

# Test endpoint
curl https://your-app.railway.app/api/health
```

### Rollback with Deployment

If feature flag is not sufficient:

1. **Revert to Previous Deployment**:
```bash
# Railway
railway rollback

# Or redeploy previous version
git revert <commit-hash>
git push
```

## Advanced: Dynamic Feature Flags (Future Enhancement)

For more sophisticated feature flag management, consider integrating a feature flag service:

### Option 1: LaunchDarkly
```python
import ldclient
from ldclient.config import Config

ldclient.set_config(Config(os.getenv("LAUNCHDARKLY_SDK_KEY")))
ld_client = ldclient.get()

# Check flag
if ld_client.variation("new-feature", {"key": user_id}, False):
    # Feature enabled for this user
    pass
```

### Option 2: Unleash (Open Source)
```python
from UnleashClient import UnleashClient

client = UnleashClient(
    url=os.getenv("UNLEASH_URL"),
    app_name="rose-healer",
    custom_headers={'Authorization': os.getenv("UNLEASH_API_KEY")}
)

if client.is_enabled("new-feature"):
    # Feature enabled
    pass
```

### Option 3: Custom Database-Backed Flags
```python
# Store flags in PostgreSQL
class FeatureFlag(BaseModel):
    name: str
    enabled: bool
    rollout_percentage: int = 100
    user_whitelist: list[str] = []

def is_feature_enabled(flag_name: str, user_id: str) -> bool:
    flag = db.query(FeatureFlag).filter_by(name=flag_name).first()
    if not flag:
        return False
    
    # Check whitelist
    if user_id in flag.user_whitelist:
        return True
    
    # Check rollout percentage
    if flag.rollout_percentage == 100:
        return flag.enabled
    
    # Consistent hashing for gradual rollout
    user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
    return (user_hash % 100) < flag.rollout_percentage
```

## Monitoring Feature Flags

### Metrics to Track

1. **Feature Usage**:
```python
from ai_companion.core.metrics import metrics

if settings.FEATURE_NEW_CAPABILITY_ENABLED:
    metrics.increment("feature.new_capability.used")
    # Feature code
```

2. **Feature Performance**:
```python
with metrics.timer("feature.new_capability.duration"):
    # Feature code
    pass
```

3. **Feature Errors**:
```python
try:
    # Feature code
except Exception as e:
    metrics.increment("feature.new_capability.error")
    raise
```

### Dashboard Queries

```sql
-- Feature usage over time
SELECT 
    date_trunc('hour', timestamp) as hour,
    COUNT(*) as usage_count
FROM metrics
WHERE metric_name = 'feature.new_capability.used'
GROUP BY hour
ORDER BY hour DESC;

-- Feature error rate
SELECT 
    COUNT(CASE WHEN metric_name = 'feature.new_capability.error' THEN 1 END) * 100.0 / 
    COUNT(CASE WHEN metric_name = 'feature.new_capability.used' THEN 1 END) as error_rate
FROM metrics
WHERE timestamp > NOW() - INTERVAL '1 hour';
```

## Testing Feature Flags

### Unit Tests
```python
import pytest
from ai_companion.settings import Settings

def test_feature_disabled():
    settings = Settings(FEATURE_NEW_CAPABILITY_ENABLED=False)
    
    with pytest.raises(ValueError, match="not enabled"):
        new_capability_function()

def test_feature_enabled():
    settings = Settings(FEATURE_NEW_CAPABILITY_ENABLED=True)
    
    result = new_capability_function()
    assert result is not None
```

### Integration Tests
```python
@pytest.mark.parametrize("flag_value", [True, False])
def test_api_with_feature_flag(flag_value):
    with patch.object(settings, 'FEATURE_NEW_CAPABILITY_ENABLED', flag_value):
        response = client.post("/api/new-capability")
        
        if flag_value:
            assert response.status_code == 200
        else:
            assert response.status_code == 404
```

## Security Considerations

### 1. Don't Expose Internal Flags
```python
# Bad: Exposing all flags to frontend
@router.get("/api/feature-flags")
def get_feature_flags():
    return settings.dict()  # Exposes everything!

# Good: Only expose user-facing flags
@router.get("/api/feature-flags")
def get_feature_flags():
    return {
        "image_generation": settings.FEATURE_IMAGE_GENERATION_ENABLED,
        "whatsapp": settings.FEATURE_WHATSAPP_ENABLED,
    }
```

### 2. Validate Flag Changes
```python
# Require authentication for flag changes
@router.post("/api/admin/feature-flags")
async def update_feature_flag(
    flag: str,
    enabled: bool,
    admin_token: str = Header(...)
):
    if admin_token != settings.ADMIN_TOKEN:
        raise HTTPException(403, "Unauthorized")
    
    # Update flag
    pass
```

### 3. Audit Flag Changes
```python
logger.info("Feature flag changed", extra={
    "flag_name": flag_name,
    "old_value": old_value,
    "new_value": new_value,
    "changed_by": user_id,
    "timestamp": datetime.now().isoformat(),
})
```

## Conclusion

The feature flags system provides:
- ✅ Zero-downtime feature rollouts
- ✅ Quick rollback capability
- ✅ Environment-specific configuration
- ✅ Gradual rollout support
- ✅ A/B testing foundation

**Current Implementation**: Simple environment-based flags (sufficient for current scale)

**Future Enhancement**: Consider dynamic flag service when:
- Need per-user feature targeting
- Want percentage-based rollouts
- Require real-time flag updates without restart
- Have multiple teams managing features

**Recommended Next Steps**:
1. Add feature flags for database migration
2. Test flag-based rollback procedures
3. Document flag usage in deployment guide
4. Monitor flag usage in production
