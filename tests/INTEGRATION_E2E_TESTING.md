# Integration and E2E Testing Guide

This guide covers the integration tests, end-to-end tests, and post-deployment smoke tests added to the Rose application.

## Overview

The test suite now includes three new categories of tests:

1. **Integration Tests** (`test_integration.py`) - Tests with real external APIs
2. **End-to-End Tests** (`test_e2e_playwright.py`) - Browser-based UI tests
3. **Post-Deployment Smoke Tests** (`test_post_deployment_smoke.py`) - Production verification

## Test Coverage Requirements

The project now enforces a **70% minimum code coverage** threshold. Tests will fail if coverage drops below this level.

```bash
# Run tests with coverage report
pytest tests/ --cov=ai_companion --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
start htmlcov\index.html  # Windows
```

## Integration Tests

### Purpose

Integration tests verify that the application works correctly with real external services:
- Groq API (LLM and Speech-to-Text)
- ElevenLabs API (Text-to-Speech)
- Qdrant (Vector Database)

### Prerequisites

```bash
# Install test dependencies
uv pip install -e ".[test]"

# Set required environment variables
export GROQ_API_KEY=your_groq_api_key
export ELEVENLABS_API_KEY=your_elevenlabs_api_key
export ELEVENLABS_VOICE_ID=your_voice_id
export QDRANT_URL=your_qdrant_url
export QDRANT_API_KEY=your_qdrant_api_key

# Windows (PowerShell)
$env:GROQ_API_KEY="your_groq_api_key"
$env:ELEVENLABS_API_KEY="your_elevenlabs_api_key"
# ... etc
```

### Running Integration Tests

```bash
# Run all integration tests
pytest tests/test_integration.py -v -m integration

# Run specific test class
pytest tests/test_integration.py::TestGroqIntegration -v
pytest tests/test_integration.py::TestElevenLabsIntegration -v
pytest tests/test_integration.py::TestQdrantIntegration -v

# Run with helper script
./tests/run_integration_tests.sh integration  # Unix/Mac
tests\run_integration_tests.bat integration   # Windows
```

### What's Tested

- **Groq Integration**
  - LLM completion with real API
  - Speech-to-text transcription
  - Circuit breaker functionality

- **ElevenLabs Integration**
  - Text-to-speech synthesis
  - Fallback mechanism
  - Circuit breaker functionality

- **Qdrant Integration**
  - Database connection
  - Memory storage and retrieval
  - Circuit breaker functionality

- **End-to-End Voice Flow**
  - Complete workflow: session → audio → transcription → LLM → TTS
  - Session continuity with memory
  - Error recovery
  - Concurrent requests

### Important Notes

⚠️ **Integration tests make real API calls and may incur costs.**

- Tests are automatically skipped if API keys are not set
- Use test/development API keys when possible
- Monitor API usage and costs
- Consider rate limits when running tests frequently

## End-to-End Tests

### Purpose

E2E tests verify the complete user experience in a real browser using Playwright.

### Prerequisites

```bash
# Install Playwright dependencies
uv pip install -e ".[playwright]"
playwright install

# Or install browsers with system dependencies
playwright install --with-deps
```

### Running E2E Tests

```bash
# Start the server first
uvicorn ai_companion.interfaces.web.app:app --port 8080

# In another terminal, run E2E tests
pytest tests/test_e2e_playwright.py -v -m e2e

# Run with visible browser (headed mode)
pytest tests/test_e2e_playwright.py -v -m e2e --headed

# Run specific test
pytest tests/test_e2e_playwright.py::TestVoiceInterfaceE2E -v --headed

# Run with helper script
./tests/run_integration_tests.sh e2e  # Unix/Mac
tests\run_integration_tests.bat e2e   # Windows
```

### What's Tested

- **Voice Interface**
  - Page loads successfully
  - Voice button is present and interactive
  - Button state transitions
  - Error message display
  - Session initialization

- **Responsive Design**
  - Mobile viewport (375x667)
  - Tablet viewport (768x1024)
  - Desktop viewport (1920x1080)

- **Accessibility**
  - Keyboard navigation
  - ARIA labels
  - Focus indicators

- **Error Handling**
  - Network errors
  - Offline indicator

- **Performance**
  - Page load time (< 5 seconds)
  - No console errors

- **Session Management**
  - Session persistence on refresh
  - Multiple tabs with different sessions

- **Visual Regression**
  - Homepage screenshot
  - Voice button screenshot

### Screenshots

E2E tests generate screenshots in `tests/screenshots/`:
- `homepage.png` - Full page screenshot
- `voice-button.png` - Voice button screenshot

These can be used for visual regression testing in CI/CD.

## Post-Deployment Smoke Tests

### Purpose

Smoke tests verify critical functionality after deployment to production or staging.

### Prerequisites

```bash
# Install test dependencies (no special dependencies needed)
uv pip install -e ".[test]"

# Set deployed URL (optional, defaults to localhost)
export DEPLOYED_URL=https://your-app.railway.app

# Windows (PowerShell)
$env:DEPLOYED_URL="https://your-app.railway.app"
```

### Running Smoke Tests

```bash
# Run against local server
pytest tests/test_post_deployment_smoke.py -v -m smoke

# Run against deployed instance
DEPLOYED_URL=https://your-app.railway.app pytest tests/test_post_deployment_smoke.py -v -m smoke

# Run with helper script
./tests/run_integration_tests.sh smoke  # Unix/Mac
tests\run_integration_tests.bat smoke   # Windows

# Run comprehensive readiness check
pytest tests/test_post_deployment_smoke.py::TestDeploymentReadiness -v -m smoke
```

### What's Tested

- **Deployment Health**
  - Health endpoint responds
  - All services are healthy
  - Response time < 5 seconds

- **Critical Endpoints**
  - Session start endpoint
  - Voice process endpoint exists
  - API documentation (if enabled)

- **Frontend Deployment**
  - Frontend loads successfully
  - Static assets accessible

- **Security**
  - Security headers present
  - CORS configuration
  - Rate limiting

- **Data Persistence**
  - Session persistence
  - Unique session IDs

- **Error Handling**
  - 404 handling
  - Method not allowed
  - Invalid JSON handling

- **Monitoring**
  - Request ID in responses

- **Performance**
  - Health check < 2 seconds average
  - Session creation < 3 seconds average

### CI/CD Integration

Add to your GitHub Actions workflow:

```yaml
- name: Run smoke tests
  env:
    DEPLOYED_URL: ${{ steps.deploy.outputs.url }}
  run: pytest tests/test_post_deployment_smoke.py -v -m smoke
```

## Running All Tests

### Quick Commands

```bash
# Run all tests (unit + integration + smoke)
./tests/run_integration_tests.sh all  # Unix/Mac
tests\run_integration_tests.bat all   # Windows

# Run only unit tests (no API keys needed)
pytest tests/ -v -m "not integration and not e2e"

# Run with coverage
pytest tests/ -v -m "not integration and not e2e" --cov=ai_companion --cov-report=html
```

### Test Markers

Tests are organized with pytest markers:

- `@pytest.mark.unit` - Unit tests (fast, no external dependencies)
- `@pytest.mark.integration` - Integration tests (requires API keys)
- `@pytest.mark.e2e` - End-to-end tests (requires browser)
- `@pytest.mark.smoke` - Smoke tests (post-deployment)
- `@pytest.mark.slow` - Slow tests (can be skipped)

```bash
# Run specific marker
pytest tests/ -v -m unit
pytest tests/ -v -m integration
pytest tests/ -v -m e2e
pytest tests/ -v -m smoke

# Exclude specific marker
pytest tests/ -v -m "not integration"
pytest tests/ -v -m "not slow"

# Combine markers
pytest tests/ -v -m "unit or smoke"
pytest tests/ -v -m "not integration and not e2e"
```

## Troubleshooting

### Integration Tests Fail with API Errors

**Problem:** Tests fail with authentication or API errors.

**Solution:**
1. Verify API keys are set correctly
2. Check API key permissions and quotas
3. Verify network connectivity to external services
4. Check service status pages

### E2E Tests Fail to Start

**Problem:** Playwright tests fail with browser errors.

**Solution:**
```bash
# Reinstall browsers
playwright install --with-deps

# Check if server is running
curl http://localhost:8080/api/health

# Start server if not running
uvicorn ai_companion.interfaces.web.app:app --port 8080
```

### Smoke Tests Fail Against Deployed Instance

**Problem:** Smoke tests fail when testing deployed application.

**Solution:**
1. Verify DEPLOYED_URL is set correctly
2. Check if application is actually deployed and running
3. Verify environment variables are set in deployment
4. Check deployment logs for errors
5. Verify network connectivity to deployed instance

### Coverage Below 70%

**Problem:** Tests fail with coverage below threshold.

**Solution:**
1. Identify uncovered code: `pytest --cov=ai_companion --cov-report=html`
2. Add tests for uncovered modules
3. Focus on core functionality first
4. Exclude non-critical code from coverage (update pytest.ini)

### Tests Are Too Slow

**Problem:** Test suite takes too long to run.

**Solution:**
```bash
# Run only fast tests
pytest tests/ -v -m "not slow and not integration and not e2e"

# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest tests/ -v -n auto

# Skip integration tests in development
pytest tests/ -v -m "not integration"
```

## Best Practices

### For Integration Tests

1. **Use test API keys** when available
2. **Monitor API usage** to avoid unexpected costs
3. **Run sparingly** - not on every commit
4. **Mock in unit tests** - use integration tests for critical paths only
5. **Clean up test data** after tests complete

### For E2E Tests

1. **Keep tests focused** - test critical user flows only
2. **Use stable selectors** - prefer data-testid over CSS classes
3. **Handle timing** - use Playwright's auto-waiting features
4. **Take screenshots** on failure for debugging
5. **Run in CI** - catch UI regressions early

### For Smoke Tests

1. **Keep tests fast** - smoke tests should complete in < 2 minutes
2. **Test critical paths** only - not comprehensive testing
3. **Run after every deployment** - automate in CI/CD
4. **Alert on failures** - smoke test failures indicate production issues
5. **Test production-like environment** - use staging for smoke tests

## Coverage Goals

Current coverage requirements:
- **Minimum:** 70% overall coverage
- **Target:** 80% coverage for core modules
- **Exclusions:** Chainlit/WhatsApp interfaces, test files

Focus coverage on:
- Core business logic (`src/ai_companion/core/`)
- Graph nodes (`src/ai_companion/graph/`)
- Memory modules (`src/ai_companion/modules/memory/`)
- Speech modules (`src/ai_companion/modules/speech/`)
- API routes (`src/ai_companion/interfaces/web/routes/`)

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Python Documentation](https://playwright.dev/python/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Integration Testing Best Practices](https://martinfowler.com/bliki/IntegrationTest.html)
- [E2E Testing Best Practices](https://playwright.dev/docs/best-practices)

## Support

For issues with tests:
1. Check this documentation
2. Review test output and error messages
3. Check individual test file docstrings
4. Review the main tests/README.md
5. Check CI/CD logs for failures
