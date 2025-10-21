# GitHub Actions CI/CD Configuration

This directory contains the CI/CD pipeline configuration for the Rose the Healer Shaman application.

## Workflows

### 1. Tests and Deployment (`test.yml`)

Main CI/CD pipeline that runs on push and pull requests to `main` and `develop` branches.

**Jobs:**
- **test**: Runs unit tests with coverage reporting
- **smoke-tests**: Pre-deployment validation tests
- **deploy**: Deploys to Railway (only on main branch)
- **integration-tests**: Optional integration tests with real APIs

### 2. Status Check (`status-check.yml`)

PR validation workflow that checks:
- PR title follows conventional commits format
- Required files are present
- No large files are committed

## Required GitHub Secrets

Configure these secrets in your GitHub repository settings (Settings → Secrets and variables → Actions):

### API Keys (Required for all workflows)
- `GROQ_API_KEY`: Groq API key for LLM and STT
- `ELEVENLABS_API_KEY`: ElevenLabs API key for TTS
- `ELEVENLABS_VOICE_ID`: ElevenLabs voice ID
- `QDRANT_URL`: Qdrant Cloud URL
- `QDRANT_API_KEY`: Qdrant API key

### Deployment (Required for deploy job)
- `RAILWAY_TOKEN`: Railway CLI authentication token
- `RAILWAY_URL`: Deployed application URL (e.g., https://your-app.railway.app)

### Coverage Reporting (Optional)
- `CODECOV_TOKEN`: Codecov upload token for coverage reports

## Setting Up Secrets

### 1. API Keys

Get your API keys from:
- Groq: https://console.groq.com/keys
- ElevenLabs: https://elevenlabs.io/app/settings/api-keys
- Qdrant: https://cloud.qdrant.io/

Add them to GitHub:
```bash
# Navigate to: Repository → Settings → Secrets and variables → Actions → New repository secret
```

### 2. Railway Token

Get your Railway token:
```bash
# Install Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# Login and get token
railway login
railway whoami --token
```

Add the token to GitHub secrets as `RAILWAY_TOKEN`.

### 3. Railway URL

After deploying to Railway, get your application URL:
```bash
railway status
```

Add the URL to GitHub secrets as `RAILWAY_URL` (e.g., `https://rose-production.railway.app`).

### 4. Codecov Token (Optional)

1. Sign up at https://codecov.io with your GitHub account
2. Add your repository
3. Copy the upload token
4. Add it to GitHub secrets as `CODECOV_TOKEN`

## Workflow Triggers

### Automatic Triggers

- **Push to main**: Runs all tests, smoke tests, and deploys to production
- **Push to develop**: Runs tests and integration tests
- **Pull Request**: Runs tests and status checks

### Manual Triggers

You can manually trigger workflows from the Actions tab:
1. Go to Actions → Select workflow
2. Click "Run workflow"
3. Select branch and run

## Coverage Requirements

The pipeline enforces a minimum code coverage of **70%**. Tests will fail if coverage drops below this threshold.

Coverage reports are:
- Uploaded to Codecov (if token is configured)
- Available as artifacts in the workflow run
- Displayed in the workflow summary

## Deployment Process

### Automatic Deployment (Main Branch)

1. Push to `main` branch
2. Tests run automatically
3. Smoke tests validate deployment readiness
4. If all tests pass, deploys to Railway
5. Post-deployment tests verify the deployment

### Manual Deployment

```bash
# Install Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# Login
railway login

# Deploy
railway up --service rose-production
```

## Troubleshooting

### Tests Failing in CI but Passing Locally

- Ensure all environment variables are set in GitHub secrets
- Check that dependencies are properly specified in `pyproject.toml`
- Review the workflow logs for specific error messages

### Deployment Failing

- Verify `RAILWAY_TOKEN` is valid and not expired
- Check Railway dashboard for deployment errors
- Ensure all required environment variables are set in Railway
- Verify Railway service name matches the workflow configuration

### Coverage Upload Failing

- Verify `CODECOV_TOKEN` is set correctly
- Check Codecov dashboard for upload errors
- Coverage upload failures don't fail the build (fail_ci_if_error: false)

## Workflow Customization

### Changing Coverage Threshold

Edit `.github/workflows/test.yml`:
```yaml
- name: Check coverage threshold
  run: |
    uv run pytest tests/ \
      --cov=ai_companion \
      --cov-fail-under=70 \  # Change this value
      -m "not slow and not integration" \
      --quiet
```

### Changing Railway Service Name

Edit `.github/workflows/test.yml`:
```yaml
- name: Deploy to Railway
  env:
    RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
  run: |
    railway up --service rose-production  # Change service name here
```

### Adding New Test Markers

1. Add marker to `tests/pytest.ini`:
```ini
markers =
    your_marker: description of your marker
```

2. Use in workflow:
```yaml
- name: Run your tests
  run: |
    uv run pytest tests/ -v -m "your_marker"
```

## Best Practices

1. **Always run tests locally before pushing**
   ```bash
   uv run pytest tests/ -v
   ```

2. **Check coverage locally**
   ```bash
   uv run pytest tests/ --cov=ai_companion --cov-report=html
   ```

3. **Use conventional commit messages**
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `test:` for tests
   - `chore:` for maintenance

4. **Review workflow logs**
   - Check Actions tab for detailed logs
   - Download artifacts for coverage reports
   - Review failed test output

## Monitoring

### GitHub Actions Dashboard

Monitor workflow runs at: `https://github.com/YOUR_USERNAME/YOUR_REPO/actions`

### Railway Dashboard

Monitor deployments at: `https://railway.app/dashboard`

### Codecov Dashboard

Monitor coverage trends at: `https://codecov.io/gh/YOUR_USERNAME/YOUR_REPO`

## Support

For issues with:
- **GitHub Actions**: Check workflow logs and GitHub Actions documentation
- **Railway**: Check Railway dashboard and Railway documentation
- **Codecov**: Check Codecov dashboard and Codecov documentation
- **Tests**: Review test output and pytest documentation
