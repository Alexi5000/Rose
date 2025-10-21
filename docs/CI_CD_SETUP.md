# CI/CD Pipeline Setup

This document describes the CI/CD pipeline configuration for the Rose the Healer Shaman application.

## Overview

The CI/CD pipeline automates testing, coverage reporting, and deployment using GitHub Actions. It ensures code quality, prevents regressions, and enables safe, automated deployments to Railway.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Push/PR                            │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐  ┌────────▼─────────┐
│  Test Job      │  │ Integration Tests │
│  - Lint        │  │ (Optional)        │
│  - Format      │  │                   │
│  - Unit Tests  │  └───────────────────┘
│  - Coverage    │
└───────┬────────┘
        │
┌───────▼────────┐
│ Smoke Tests    │
│ - Deployment   │
│ - Docker Build │
│ - Health Check │
└───────┬────────┘
        │
┌───────▼────────┐
│ Deploy Job     │
│ (main only)    │
│ - Railway      │
│ - Verify       │
└────────────────┘
```

## Workflows

### 1. Test Workflow (`.github/workflows/test.yml`)

Main workflow that runs on every push and pull request.

#### Jobs

##### Test Job
- **Triggers**: All pushes and PRs
- **Steps**:
  1. Checkout code
  2. Set up Python 3.12
  3. Install uv package manager
  4. Install dependencies
  5. Run linting (ruff)
  6. Run formatting check (ruff)
  7. Run unit tests with coverage
  8. Upload coverage to Codecov
  9. Check 70% coverage threshold

##### Smoke Tests Job
- **Triggers**: After test job passes
- **Steps**:
  1. Run deployment validation tests
  2. Build Docker image
  3. Test Docker container startup
  4. Verify health endpoint

##### Deploy Job
- **Triggers**: Only on main branch pushes, after tests pass
- **Steps**:
  1. Install Railway CLI
  2. Deploy to Railway
  3. Wait for deployment
  4. Verify deployment health
  5. Run post-deployment smoke tests

##### Integration Tests Job (Optional)
- **Triggers**: PRs and develop branch
- **Steps**:
  1. Run integration tests with real APIs
  2. Allowed to fail (non-blocking)

## Required GitHub Secrets

Configure these secrets in your GitHub repository settings:

### API Keys (Required for Tests)
- `GROQ_API_KEY`: Groq API key for LLM/STT
- `ELEVENLABS_API_KEY`: ElevenLabs API key for TTS
- `ELEVENLABS_VOICE_ID`: ElevenLabs voice ID
- `QDRANT_URL`: Qdrant instance URL (cloud or self-hosted)
- `QDRANT_API_KEY`: Qdrant API key (optional for self-hosted without auth)

### Deployment (Required for Deploy Job)
- `RAILWAY_TOKEN`: Railway API token for deployment
- `RAILWAY_URL`: Deployed application URL (e.g., https://rose.railway.app)

### Coverage Reporting (Optional)
- `CODECOV_TOKEN`: Codecov token for coverage reporting

## Setting Up Secrets

### 1. GitHub Repository Secrets

Go to your repository settings:
```
Settings → Secrets and variables → Actions → New repository secret
```

Add each secret with its corresponding value.

### 2. Railway Token

Get your Railway token:
```bash
# Install Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# Login
railway login

# Get token
railway whoami
```

Copy the token and add it as `RAILWAY_TOKEN` secret.

### 3. Codecov Token

1. Go to [codecov.io](https://codecov.io)
2. Sign in with GitHub
3. Add your repository
4. Copy the upload token
5. Add it as `CODECOV_TOKEN` secret

### 4. Qdrant Setup Options

You have two options for Qdrant in CI:

**Option A: Qdrant Cloud (Recommended for CI)**
- Sign up at [cloud.qdrant.io](https://cloud.qdrant.io)
- Create a cluster (free tier available)
- Get your cluster URL and API key
- Add as `QDRANT_URL` and `QDRANT_API_KEY` secrets

**Option B: Self-Hosted Qdrant in CI**
- Run Qdrant as a service in GitHub Actions
- No API key needed
- See example workflow below:

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - 6333:6333
    env:
      QDRANT__SERVICE__GRPC_PORT: 6334
```

Then set `QDRANT_URL=http://localhost:6333` in the workflow.

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit`: Unit tests (default)
- `@pytest.mark.integration`: Integration tests with real APIs
- `@pytest.mark.slow`: Slow-running tests
- `@pytest.mark.smoke`: Smoke tests for deployment

### Running Tests Locally

```bash
# All unit tests
pytest tests/ -v

# Exclude slow tests
pytest tests/ -v -m "not slow"

# Only smoke tests
pytest tests/ -v -m smoke

# With coverage
pytest tests/ --cov=ai_companion --cov-report=html

# Check coverage threshold
pytest tests/ --cov=ai_companion --cov-fail-under=70
```

## Coverage Configuration

### Coverage Targets

- **Project Coverage**: 70% minimum
- **Patch Coverage**: 70% minimum for new code
- **Threshold**: 2% allowed decrease

### Excluded from Coverage

- Test files (`tests/`)
- Notebooks (`notebooks/`)
- Chainlit interface (UI-specific)
- WhatsApp interface (frozen feature)

### Coverage Reports

Coverage reports are:
1. Uploaded to Codecov for tracking
2. Saved as GitHub Actions artifacts (30 days)
3. Displayed in PR comments (via Codecov)

## Deployment Process

### Automatic Deployment

Deployments happen automatically when:
1. Code is pushed to `main` branch
2. All tests pass
3. Smoke tests pass
4. Coverage threshold is met

### Manual Deployment

To deploy manually:

```bash
# Using Railway CLI
railway up --service rose-production

# Or trigger GitHub Actions manually
# Go to Actions → Test and Deployment → Run workflow
```

### Deployment Verification

After deployment, the pipeline:
1. Waits 30 seconds for Railway to start
2. Checks health endpoint
3. Runs post-deployment smoke tests
4. Reports success/failure

### Rollback Procedure

If deployment fails:

```bash
# Using Railway CLI
railway rollback

# Or via Railway dashboard
# Go to Deployments → Select previous deployment → Redeploy
```

## Monitoring and Alerts

### GitHub Actions Notifications

Configure notifications:
```
Settings → Notifications → Actions
```

Options:
- Email on workflow failure
- Slack/Discord webhooks
- GitHub mobile app notifications

### Codecov Notifications

Codecov will:
- Comment on PRs with coverage changes
- Send notifications on coverage drops
- Track coverage trends over time

## Troubleshooting

### Tests Fail in CI but Pass Locally

**Possible causes:**
1. Missing environment variables in GitHub secrets
2. Different Python version (CI uses 3.12)
3. Missing dependencies in `pyproject.toml`
4. Timing issues with async tests

**Solutions:**
```bash
# Test with same Python version
python --version  # Should be 3.12+

# Clean install dependencies
rm -rf .venv
uv sync
uv pip install -e ".[test]"

# Run tests with same markers as CI
pytest tests/ -v -m "not slow and not integration"
```

### Coverage Below Threshold

**Solutions:**
1. Add tests for uncovered code
2. Remove dead code
3. Add `# pragma: no cover` for unreachable code
4. Check `pytest.ini` for excluded paths

### Deployment Fails

**Check:**
1. Railway token is valid
2. Railway service name is correct
3. Environment variables are set in Railway
4. Railway has sufficient resources
5. Health check endpoint is accessible

**Debug:**
```bash
# Check Railway logs
railway logs

# Check Railway status
railway status

# Test health endpoint
curl https://your-app.railway.app/api/health
```

### Docker Build Fails

**Common issues:**
1. Missing files in `.dockerignore`
2. Incorrect Python version in Dockerfile
3. Missing system dependencies
4. Build context too large

**Test locally:**
```bash
# Build Docker image
docker build -t rose-test .

# Run container
docker run -p 8080:8080 rose-test

# Check logs
docker logs <container-id>
```

## Best Practices

### 1. Branch Protection

Configure branch protection for `main`:
```
Settings → Branches → Add rule
```

Rules:
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- ✅ Require review from code owners
- ✅ Require linear history

### 2. Pull Request Workflow

1. Create feature branch from `develop`
2. Make changes and commit
3. Push and create PR
4. Wait for CI to pass
5. Request review
6. Merge to `develop`
7. Merge `develop` to `main` for deployment

### 3. Test Writing

- Write tests before fixing bugs
- Aim for 80%+ coverage on new code
- Use descriptive test names
- Mock external services
- Keep tests fast (< 1 second each)

### 4. Deployment Safety

- Always test in staging first
- Monitor logs after deployment
- Have rollback plan ready
- Deploy during low-traffic periods
- Announce deployments to team

## Performance Optimization

### Caching

The workflow uses caching for:
- Python dependencies (uv cache)
- Docker layers (BuildKit)

### Parallel Jobs

Jobs run in parallel when possible:
- Test and Integration Tests run together
- Deploy only runs after all tests pass

### Selective Testing

- Unit tests run on every commit
- Integration tests run on PRs only
- Deployment tests run before deploy
- Full test suite runs on main branch

## Maintenance

### Regular Updates

Update dependencies monthly:
```bash
# Update Python packages
uv sync --upgrade

# Update GitHub Actions
# Check for new versions in .github/workflows/
```

### Review Metrics

Monthly review:
- Test execution time trends
- Coverage trends
- Deployment success rate
- Failure patterns

### Clean Up

Quarterly cleanup:
- Remove unused tests
- Archive old coverage reports
- Clean up GitHub Actions artifacts
- Review and update documentation

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Codecov Documentation](https://docs.codecov.com/)
- [Railway Documentation](https://docs.railway.app/)
- [pytest Documentation](https://docs.pytest.org/)
- [uv Documentation](https://github.com/astral-sh/uv)

## Support

For CI/CD issues:
1. Check GitHub Actions logs
2. Review this documentation
3. Check Railway logs
4. Review test output locally
5. Contact DevOps team

## Changelog

### 2024-01-20
- Initial CI/CD pipeline setup
- Added test, smoke test, and deploy jobs
- Configured Codecov integration
- Added comprehensive smoke tests
- Created documentation
