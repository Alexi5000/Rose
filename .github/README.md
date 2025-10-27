# GitHub Actions CI/CD Configuration

This directory contains the CI/CD pipeline configuration for the Rose the Healer Shaman application.

## Workflows

### 1. CI/CD Pipeline (`ci-cd.yml`)

Comprehensive CI/CD pipeline that runs on push and pull requests to `main` and `develop` branches.

**Jobs:**
- **code-quality**: Runs ruff linting, formatting checks, and mypy type checking
- **unit-tests**: Runs unit tests with coverage reporting (70% threshold)
  - Uploads coverage to Codecov
  - Generates HTML coverage reports as artifacts
  - Comments on PRs with failure details
- **integration-tests**: Runs integration tests with real API calls (non-blocking)
  - Only runs on develop branch or PRs
  - Uses real API credentials from GitHub Secrets
- **smoke-tests**: Pre-deployment validation tests
  - Builds Docker image
  - Tests container startup
  - Verifies health endpoint
  - Only runs for main branch or PRs to main
- **deploy-production**: Deploys to Railway production
  - Installs Railway CLI
  - Deploys to production service
  - Waits for deployment to stabilize (30 seconds)
  - Verifies deployment health with retries
  - Runs post-deployment smoke tests
  - Creates GitHub issue on failure
  - Only runs on push to main
- **workflow-summary**: Generates workflow summary with job results

**Error Handling:**
- Uploads test results as artifacts on failure
- Comments on PRs with failure details
- Creates GitHub issues for deployment failures
- Provides detailed error logs for troubleshooting

### 2. Status Check (`status-check.yml`)

PR validation workflow that checks:
- PR title follows conventional commits format
- Required files are present
- No large files are committed

## Required GitHub Secrets

Configure these secrets in your GitHub repository settings (Settings → Secrets and variables → Actions):

### API Keys (Required for all workflows)

| Secret Name | Description | Required | Rotation Period |
|-------------|-------------|----------|-----------------|
| `GROQ_API_KEY` | Groq API key for LLM inference and speech-to-text | Yes | 90 days |
| `ELEVENLABS_API_KEY` | ElevenLabs API key for text-to-speech | Yes | 90 days |
| `ELEVENLABS_VOICE_ID` | ElevenLabs voice ID (e.g., `21m00Tcm4TlvDq8ikWAM`) | Yes | N/A |
| `QDRANT_URL` | Qdrant Cloud URL (e.g., `https://xyz.qdrant.io`) | Yes | N/A |
| `QDRANT_API_KEY` | Qdrant API key for vector database access | Yes | 90 days |
| `TOGETHER_API_KEY` | Together AI API key for image generation (optional) | No | 90 days |

### Deployment (Required for deploy job)

| Secret Name | Description | Required | Rotation Period |
|-------------|-------------|----------|-----------------|
| `RAILWAY_TOKEN` | Railway CLI authentication token | Yes | 180 days |
| `RAILWAY_PRODUCTION_URL` | Production application URL (e.g., `https://rose-production.railway.app`) | Yes | N/A |
| `RAILWAY_STAGING_URL` | Staging application URL (future use) | No | N/A |

### Coverage Reporting (Optional)

| Secret Name | Description | Required | Rotation Period |
|-------------|-------------|----------|-----------------|
| `CODECOV_TOKEN` | Codecov upload token for coverage reports | No | 365 days |

### Notifications (Optional)

| Secret Name | Description | Required | Rotation Period |
|-------------|-------------|----------|-----------------|
| `SLACK_WEBHOOK_URL` | Slack webhook URL for deployment notifications | No | 180 days |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL for deployment notifications | No | 180 days |

## Setting Up Secrets

### Quick Setup Checklist

Use this checklist to ensure all required secrets are configured:

- [ ] **API Keys**
  - [ ] `GROQ_API_KEY` - Obtained from Groq Console
  - [ ] `ELEVENLABS_API_KEY` - Obtained from ElevenLabs Dashboard
  - [ ] `ELEVENLABS_VOICE_ID` - Voice ID from ElevenLabs
  - [ ] `QDRANT_URL` - Qdrant Cloud cluster URL
  - [ ] `QDRANT_API_KEY` - Qdrant API key
  - [ ] `TOGETHER_API_KEY` - (Optional) Together AI API key

- [ ] **Deployment**
  - [ ] `RAILWAY_TOKEN` - Railway CLI token
  - [ ] `RAILWAY_PRODUCTION_URL` - Production deployment URL
  - [ ] `RAILWAY_STAGING_URL` - (Optional) Staging deployment URL

- [ ] **Coverage & Notifications**
  - [ ] `CODECOV_TOKEN` - (Optional) Codecov upload token
  - [ ] `SLACK_WEBHOOK_URL` - (Optional) Slack webhook
  - [ ] `DISCORD_WEBHOOK_URL` - (Optional) Discord webhook

- [ ] **Verification**
  - [ ] All secrets added to GitHub repository settings
  - [ ] Test workflow triggered successfully
  - [ ] No secret-related errors in workflow logs

### Detailed Setup Instructions

#### 1. Groq API Key

**Obtaining the Key:**
1. Visit https://console.groq.com/keys
2. Sign in or create an account
3. Click "Create API Key"
4. Copy the generated key (starts with `gsk_`)
5. Store securely - it won't be shown again

**Adding to GitHub:**
1. Go to your repository on GitHub
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `GROQ_API_KEY`
5. Value: Paste your Groq API key
6. Click **Add secret**

#### 2. ElevenLabs API Key and Voice ID

**Obtaining the API Key:**
1. Visit https://elevenlabs.io/app/settings/api-keys
2. Sign in or create an account
3. Click "Create API Key" or copy existing key
4. Copy the key (starts with `sk_`)

**Obtaining the Voice ID:**
1. Visit https://elevenlabs.io/app/voice-library
2. Select a voice or use your cloned voice
3. Copy the Voice ID (e.g., `21m00Tcm4TlvDq8ikWAM`)
4. Or use the default voice ID: `21m00Tcm4TlvDq8ikWAM`

**Adding to GitHub:**
1. Add `ELEVENLABS_API_KEY` with your API key
2. Add `ELEVENLABS_VOICE_ID` with your voice ID

#### 3. Qdrant Cloud Credentials

**Obtaining Credentials:**
1. Visit https://cloud.qdrant.io/
2. Sign in or create an account
3. Create a cluster or use existing cluster
4. Copy the **Cluster URL** (e.g., `https://xyz-abc123.qdrant.io`)
5. Go to **API Keys** section
6. Create or copy an API key

**Adding to GitHub:**
1. Add `QDRANT_URL` with your cluster URL
2. Add `QDRANT_API_KEY` with your API key

#### 4. Together AI API Key (Optional)

**Obtaining the Key:**
1. Visit https://api.together.xyz/settings/api-keys
2. Sign in or create an account
3. Click "Create API Key"
4. Copy the generated key

**Adding to GitHub:**
1. Add `TOGETHER_API_KEY` with your API key

#### 5. Railway Token

**Installing Railway CLI:**

On macOS/Linux:
```bash
curl -fsSL https://railway.app/install.sh | sh
```

On Windows (PowerShell):
```powershell
iwr https://railway.app/install.ps1 | iex
```

**Obtaining the Token:**
```bash
# Login to Railway (opens browser)
railway login

# Get your authentication token
railway whoami --token
```

**Adding to GitHub:**
1. Copy the token from the CLI output
2. Add `RAILWAY_TOKEN` with your token
3. **Important**: This token has full access to your Railway account - keep it secure!

#### 6. Railway Production URL

**Obtaining the URL:**

After deploying your application to Railway:

```bash
# Link to your Railway project
railway link

# Get the deployment URL
railway status
```

Or from Railway Dashboard:
1. Visit https://railway.app/dashboard
2. Select your project
3. Click on your service
4. Copy the public URL from the **Settings** → **Networking** section

**Adding to GitHub:**
1. Add `RAILWAY_PRODUCTION_URL` with your production URL
2. Format: `https://your-app.railway.app` (no trailing slash)

#### 7. Codecov Token (Optional)

**Obtaining the Token:**
1. Visit https://codecov.io
2. Sign in with your GitHub account
3. Click **Add Repository**
4. Select your repository
5. Copy the **Upload Token** from the setup instructions

**Adding to GitHub:**
1. Add `CODECOV_TOKEN` with your upload token

#### 8. Slack Webhook (Optional)

**Creating a Webhook:**
1. Visit https://api.slack.com/apps
2. Create a new app or select existing app
3. Enable **Incoming Webhooks**
4. Click **Add New Webhook to Workspace**
5. Select the channel for notifications
6. Copy the webhook URL

**Adding to GitHub:**
1. Add `SLACK_WEBHOOK_URL` with your webhook URL

#### 9. Discord Webhook (Optional)

**Creating a Webhook:**
1. Open Discord and go to your server
2. Right-click the channel → **Edit Channel**
3. Go to **Integrations** → **Webhooks**
4. Click **New Webhook**
5. Copy the webhook URL

**Adding to GitHub:**
1. Add `DISCORD_WEBHOOK_URL` with your webhook URL

## Secret Rotation Procedures

Regular secret rotation is a critical security practice. Follow these procedures to rotate secrets safely.

### Rotation Schedule

| Secret Type | Rotation Period | Priority |
|-------------|-----------------|----------|
| API Keys (Groq, ElevenLabs, Qdrant, Together) | Every 90 days | High |
| Railway Token | Every 180 days | High |
| Codecov Token | Every 365 days | Medium |
| Webhook URLs (Slack, Discord) | Every 180 days | Low |

### General Rotation Process

1. **Generate New Secret**
   - Create new API key/token in the service provider's dashboard
   - Keep the old secret active during transition

2. **Update GitHub Secret**
   - Go to: **Settings** → **Secrets and variables** → **Actions**
   - Click on the secret name
   - Click **Update secret**
   - Paste the new value
   - Click **Update secret**

3. **Verify Functionality**
   - Trigger a test workflow run
   - Monitor for any authentication errors
   - Check that all services are working correctly

4. **Revoke Old Secret**
   - Once verified, revoke the old secret in the service provider's dashboard
   - Document the rotation in your security log

5. **Update Local Environments**
   - Update `.env` files in local development environments
   - Notify team members to update their local secrets

### Service-Specific Rotation Instructions

#### Rotating Groq API Key

```bash
# 1. Generate new key at https://console.groq.com/keys
# 2. Update GitHub secret: GROQ_API_KEY
# 3. Test with a workflow run
# 4. Revoke old key in Groq Console
# 5. Update local .env files
```

**Verification:**
```bash
# Test locally
export GROQ_API_KEY="new_key_here"
uv run pytest tests/unit/test_core.py -v
```

#### Rotating ElevenLabs API Key

```bash
# 1. Generate new key at https://elevenlabs.io/app/settings/api-keys
# 2. Update GitHub secret: ELEVENLABS_API_KEY
# 3. Test with a workflow run
# 4. Revoke old key in ElevenLabs Dashboard
# 5. Update local .env files
```

**Verification:**
```bash
# Test locally
export ELEVENLABS_API_KEY="new_key_here"
uv run pytest tests/unit/modules/test_speech.py -v
```

#### Rotating Qdrant API Key

```bash
# 1. Generate new key at https://cloud.qdrant.io/
# 2. Update GitHub secret: QDRANT_API_KEY
# 3. Test with a workflow run
# 4. Revoke old key in Qdrant Dashboard
# 5. Update local .env files
```

**Verification:**
```bash
# Test locally
export QDRANT_API_KEY="new_key_here"
uv run pytest tests/unit/modules/test_memory.py -v
```

#### Rotating Railway Token

**Important**: Railway tokens have full account access. Rotate carefully.

```bash
# 1. Generate new token
railway login
railway whoami --token

# 2. Update GitHub secret: RAILWAY_TOKEN
# 3. Test deployment with a non-production branch
# 4. Verify deployment succeeds
# 5. Old token is automatically invalidated after logout
```

**Verification:**
```bash
# Test new token locally
export RAILWAY_TOKEN="new_token_here"
railway status
```

#### Rotating Codecov Token

```bash
# 1. Regenerate token at https://codecov.io/gh/YOUR_ORG/YOUR_REPO/settings
# 2. Update GitHub secret: CODECOV_TOKEN
# 3. Test with a workflow run
# 4. Old token is automatically revoked
```

### Emergency Rotation (Compromised Secrets)

If a secret is compromised, follow these steps immediately:

1. **Immediate Revocation**
   ```bash
   # Revoke the compromised secret in the service provider's dashboard
   # This takes priority over everything else
   ```

2. **Generate New Secret**
   ```bash
   # Create a new secret immediately
   # Use a different format/pattern if possible
   ```

3. **Update GitHub**
   ```bash
   # Update the GitHub secret with the new value
   # Do this within minutes of revocation
   ```

4. **Verify All Services**
   ```bash
   # Run test workflows to ensure everything works
   # Check production services are functioning
   ```

5. **Audit Access**
   ```bash
   # Review service logs for unauthorized access
   # Check for any suspicious activity
   # Document the incident
   ```

6. **Notify Team**
   ```bash
   # Inform team members of the compromise
   # Ensure everyone updates their local environments
   # Review security practices
   ```

### Rotation Checklist Template

Use this checklist when rotating secrets:

```markdown
## Secret Rotation: [SECRET_NAME] - [DATE]

- [ ] **Preparation**
  - [ ] Scheduled maintenance window (if needed)
  - [ ] Team notified of rotation
  - [ ] Backup of current configuration

- [ ] **Rotation**
  - [ ] New secret generated
  - [ ] GitHub secret updated
  - [ ] Test workflow triggered
  - [ ] Workflow passed successfully

- [ ] **Verification**
  - [ ] Production services functioning
  - [ ] No authentication errors in logs
  - [ ] Coverage/monitoring still working

- [ ] **Cleanup**
  - [ ] Old secret revoked
  - [ ] Local environments updated
  - [ ] Team confirmed updates
  - [ ] Rotation documented

- [ ] **Next Rotation**
  - [ ] Next rotation date: [DATE + ROTATION_PERIOD]
  - [ ] Calendar reminder set
```

### Automated Rotation Reminders

Set up calendar reminders for secret rotation:

```bash
# API Keys: Every 90 days
# Railway Token: Every 180 days
# Codecov Token: Every 365 days
```

**Recommended Tools:**
- Google Calendar with email reminders
- GitHub Issues with due dates
- Project management tools (Jira, Linear, etc.)

### Security Best Practices

1. **Never commit secrets to version control**
   - Always use `.env` files (gitignored)
   - Use GitHub Secrets for CI/CD
   - Scan commits for accidental secret exposure

2. **Use least privilege access**
   - API keys should have minimal required permissions
   - Railway tokens should be service-specific when possible
   - Regularly audit access levels

3. **Monitor secret usage**
   - Review service logs for unusual activity
   - Set up alerts for failed authentication attempts
   - Track API usage patterns

4. **Document all secrets**
   - Maintain a secret inventory
   - Document rotation dates
   - Track who has access to what

5. **Secure secret storage**
   - Use password managers for personal copies
   - Never share secrets via email or chat
   - Use secure channels for secret distribution

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
