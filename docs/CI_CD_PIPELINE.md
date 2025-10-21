# CI/CD Pipeline Documentation

## Overview

The Rose the Healer Shaman application uses GitHub Actions for continuous integration and continuous deployment (CI/CD). The pipeline automatically tests, validates, and deploys the application to Railway on every push to the main branch.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Push/PR Event                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Status Check Workflow                         │
│  - PR title format validation                                    │
│  - Required files check                                          │
│  - Large files detection                                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Test Workflow                               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  1. Linting & Formatting                                   │ │
│  │     - Ruff linting check                                   │ │
│  │     - Ruff formatting check                                │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  2. Unit Tests                                             │ │
│  │     - Run pytest with coverage                             │ │
│  │     - Generate coverage reports (XML, HTML, terminal)      │ │
│  │     - Upload to Codecov                                    │ │
│  │     - Enforce 70% coverage threshold                       │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Smoke Tests Workflow                           │
│  - Deployment validation tests                                   │
│  - Docker build verification                                     │
│  - Container startup test                                        │
│  - Health endpoint check                                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼ (only on main branch)
┌─────────────────────────────────────────────────────────────────┐
│                    Deploy Workflow                               │
│  - Install Railway CLI                                           │
│  - Deploy to Railway                                             │
│  - Wait for deployment                                           │
│  - Verify deployment health                                      │
│  - Run post-deployment tests                                     │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Integration Tests (Optional)                        │
│  - Run on develop branch or PRs                                  │
│  - Test with real external APIs                                  │
│  - Non-blocking (failures don't stop deployment)                │
└─────────────────────────────────────────────────────────────────┘
```

## Workflows

### 1. Test Workflow (`test.yml`)

**Trigger:** Push or PR to `main` or `develop` branches

**Jobs:**

#### Job 1: Test
- **Purpose:** Run unit tests with coverage
- **Steps:**
  1. Checkout code
  2. Set up Python 3.12
  3. Install uv package manager
  4. Install dependencies
  5. Run linting checks
  6. Run formatting checks
  7. Run unit tests with coverage
  8. Upload coverage to Codecov
  9. Check coverage threshold (70%)

**Environment Variables Required:**
- `GROQ_API_KEY`
- `ELEVENLABS_API_KEY`
- `ELEVENLABS_VOICE_ID`
- `QDRANT_URL`
- `QDRANT_API_KEY`

#### Job 2: Smoke Tests
- **Purpose:** Pre-deployment validation
- **Depends on:** Test job
- **Steps:**
  1. Run deployment validation tests
  2. Build Docker image
  3. Test container startup
  4. Verify health endpoint

#### Job 3: Deploy
- **Purpose:** Deploy to Railway production
- **Depends on:** Test and Smoke Tests jobs
- **Condition:** Only runs on `main` branch push
- **Steps:**
  1. Install Railway CLI
  2. Deploy to Railway
  3. Wait for deployment
  4. Verify deployment health
  5. Run post-deployment tests

**Additional Secrets Required:**
- `RAILWAY_TOKEN`
- `RAILWAY_URL`

#### Job 4: Integration Tests
- **Purpose:** Test with real external APIs
- **Condition:** Runs on PRs or `develop` branch
- **Steps:**
  1. Run integration tests marked with `@pytest.mark.integration`
  2. Non-blocking (failures don't fail the build)

### 2. Status Check Workflow (`status-check.yml`)

**Trigger:** Pull request opened, synchronized, or reopened

**Checks:**
1. **PR Title Format:** Validates conventional commits format
   - Valid: `feat: add feature`, `fix: resolve bug`, `docs: update README`
   - Invalid: `Add feature`, `Fixed bug`

2. **Required Files:** Ensures critical files exist
   - `README.md`
   - `pyproject.toml`
   - `pytest.ini`
   - `.env.example`

3. **Large Files:** Warns about files >1MB

## Test Coverage

### Coverage Configuration

Coverage is configured in `tests/pytest.ini`:

```ini
[coverage:run]
source = src/ai_companion
omit =
    */tests/*
    */test_*.py
    */__pycache__/*
    */site-packages/*
    */interfaces/chainlit/*
    */interfaces/whatsapp/*

[coverage:report]
precision = 2
show_missing = True
skip_covered = False
```

### Coverage Thresholds

- **Minimum:** 70% overall coverage
- **Target:** 80%+ for core modules
- **Excluded:** Chainlit and WhatsApp interfaces (frozen features)

### Coverage Reports

1. **Terminal:** Displayed in workflow logs
2. **XML:** Uploaded to Codecov
3. **HTML:** Available as workflow artifact
4. **Codecov Dashboard:** Tracks coverage trends over time

## Test Markers

Tests are organized using pytest markers:

```python
@pytest.mark.unit          # Unit tests (default)
@pytest.mark.integration   # Integration tests with real APIs
@pytest.mark.slow          # Slow-running tests
@pytest.mark.smoke         # Smoke tests for deployment
```

**Usage in CI:**
```bash
# Run only unit tests (fast)
pytest tests/ -m "not slow and not integration"

# Run integration tests
pytest tests/ -m "integration"

# Run smoke tests
pytest tests/ -m "smoke"
```

## Deployment Process

### Automatic Deployment

1. **Trigger:** Push to `main` branch
2. **Prerequisites:** All tests must pass
3. **Process:**
   - Railway CLI deploys the application
   - Health check verifies deployment
   - Post-deployment tests validate functionality
4. **Rollback:** Manual rollback via Railway dashboard if needed

### Manual Deployment

```bash
# Install Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# Login
railway login

# Deploy
railway up --service rose-production

# Check status
railway status

# View logs
railway logs
```

## Environment Variables

### Required in GitHub Secrets

| Secret | Description | Where to Get |
|--------|-------------|--------------|
| `GROQ_API_KEY` | Groq API key | https://console.groq.com/keys |
| `ELEVENLABS_API_KEY` | ElevenLabs API key | https://elevenlabs.io/app/settings/api-keys |
| `ELEVENLABS_VOICE_ID` | ElevenLabs voice ID | ElevenLabs voice library |
| `QDRANT_URL` | Qdrant Cloud URL | https://cloud.qdrant.io/ |
| `QDRANT_API_KEY` | Qdrant API key | Qdrant Cloud dashboard |
| `RAILWAY_TOKEN` | Railway CLI token | `railway whoami --token` |
| `RAILWAY_URL` | Deployed app URL | Railway dashboard |
| `CODECOV_TOKEN` | Codecov upload token | https://codecov.io |

### Setting Secrets

```bash
# Navigate to GitHub repository
# Settings → Secrets and variables → Actions → New repository secret

# Add each secret with its value
```

## Monitoring and Alerts

### GitHub Actions

- **Dashboard:** `https://github.com/YOUR_USERNAME/YOUR_REPO/actions`
- **Notifications:** Configure in GitHub settings
- **Artifacts:** Coverage reports available for 30 days

### Railway

- **Dashboard:** `https://railway.app/dashboard`
- **Logs:** Real-time application logs
- **Metrics:** CPU, memory, network usage
- **Alerts:** Configure in Railway project settings

### Codecov

- **Dashboard:** `https://codecov.io/gh/YOUR_USERNAME/YOUR_REPO`
- **Coverage Trends:** Track coverage over time
- **PR Comments:** Automatic coverage reports on PRs
- **Alerts:** Configure coverage drop alerts

## Troubleshooting

### Common Issues

#### 1. Tests Failing in CI but Passing Locally

**Symptoms:**
- Tests pass locally but fail in GitHub Actions
- Import errors or module not found

**Solutions:**
```bash
# Ensure dependencies are properly specified
uv sync
uv pip install -e ".[test]"

# Run tests in clean environment
uv run pytest tests/ -v

# Check for environment-specific issues
export CI=true
pytest tests/ -v
```

#### 2. Coverage Below Threshold

**Symptoms:**
- Coverage check fails with "coverage below 70%"

**Solutions:**
```bash
# Check current coverage
uv run pytest tests/ --cov=ai_companion --cov-report=term-missing

# Identify uncovered lines
uv run pytest tests/ --cov=ai_companion --cov-report=html
# Open htmlcov/index.html

# Add tests for uncovered code
# Or adjust threshold in workflow if appropriate
```

#### 3. Deployment Failing

**Symptoms:**
- Deploy job fails
- Railway deployment errors

**Solutions:**
```bash
# Verify Railway token
railway whoami

# Check Railway service status
railway status

# View Railway logs
railway logs

# Manual deployment
railway up --service rose-production

# Check environment variables in Railway
railway variables
```

#### 4. Docker Build Failing

**Symptoms:**
- Smoke tests fail at Docker build step

**Solutions:**
```bash
# Test Docker build locally
docker build -t rose-test:latest .

# Check Dockerfile syntax
docker build --no-cache -t rose-test:latest .

# Verify dependencies
docker run -it rose-test:latest /bin/bash
```

### Debug Mode

Enable debug logging in workflows:

```yaml
- name: Run tests with debug
  env:
    PYTEST_DEBUG: 1
    LOG_LEVEL: DEBUG
  run: |
    uv run pytest tests/ -v -s --log-cli-level=DEBUG
```

## Best Practices

### 1. Pre-Push Checklist

```bash
# Run linting
uv run ruff check src/ tests/

# Run formatting
uv run ruff format src/ tests/

# Run tests locally
uv run pytest tests/ -v

# Check coverage
uv run pytest tests/ --cov=ai_companion --cov-report=term

# Build Docker image
docker build -t rose-test:latest .
```

### 2. Commit Message Format

Follow conventional commits:

```
feat: add new feature
fix: resolve bug in component
docs: update documentation
test: add unit tests
chore: update dependencies
refactor: restructure code
perf: improve performance
ci: update CI/CD pipeline
```

### 3. Pull Request Process

1. Create feature branch from `develop`
2. Make changes and commit
3. Push and create PR
4. Wait for CI checks to pass
5. Request review
6. Merge to `develop`
7. Test in develop environment
8. Merge to `main` for production deployment

### 4. Hotfix Process

For urgent production fixes:

1. Create hotfix branch from `main`
2. Make minimal fix
3. Create PR to `main`
4. Fast-track review
5. Merge and deploy
6. Backport to `develop`

## Performance Optimization

### Caching

The workflow uses caching to speed up builds:

```yaml
- name: Cache Python dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/uv
    key: ${{ runner.os }}-uv-${{ hashFiles('**/pyproject.toml') }}
```

### Parallel Execution

Jobs run in parallel when possible:
- Test and Status Check run simultaneously
- Integration tests run independently

### Selective Testing

```bash
# Run only changed tests (future enhancement)
pytest --testmon

# Run only failed tests
pytest --lf

# Run tests in parallel
pytest -n auto
```

## Security

### Secret Management

- Never commit secrets to repository
- Use GitHub Secrets for sensitive data
- Rotate secrets regularly
- Use least-privilege access

### Dependency Security

```bash
# Check for vulnerabilities
uv pip check

# Update dependencies
uv sync --upgrade

# Audit dependencies
pip-audit
```

### Code Scanning

Enable GitHub security features:
- Dependabot alerts
- Code scanning
- Secret scanning

## Metrics and KPIs

### Pipeline Metrics

- **Build Time:** Target <5 minutes
- **Test Success Rate:** Target >95%
- **Deployment Frequency:** Multiple times per day
- **Mean Time to Recovery:** Target <1 hour

### Code Quality Metrics

- **Test Coverage:** Target >70%
- **Code Duplication:** Target <5%
- **Linting Issues:** Target 0
- **Security Vulnerabilities:** Target 0

## Future Enhancements

### Planned Improvements

1. **Staging Environment**
   - Deploy to staging before production
   - Run extended tests in staging
   - Manual approval for production

2. **Performance Testing**
   - Load testing with Locust
   - Response time monitoring
   - Resource usage tracking

3. **Security Scanning**
   - SAST (Static Application Security Testing)
   - Dependency vulnerability scanning
   - Container image scanning

4. **Advanced Monitoring**
   - Application Performance Monitoring (APM)
   - Error tracking with Sentry
   - Log aggregation

5. **Automated Rollback**
   - Automatic rollback on health check failure
   - Canary deployments
   - Blue-green deployments

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Railway Documentation](https://docs.railway.app/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Codecov Documentation](https://docs.codecov.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)

## Support

For CI/CD issues:
1. Check workflow logs in GitHub Actions
2. Review this documentation
3. Check Railway dashboard for deployment issues
4. Contact DevOps team for assistance
