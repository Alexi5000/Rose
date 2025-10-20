# Rose the Healer Shaman - Testing Documentation

This directory contains comprehensive tests for the Rose transformation project, covering voice interaction, character responses, memory system, frontend, performance, and deployment validation.

## Test Structure

```
tests/
├── README.md                      # This file
├── test_core.py                   # Core utility tests (existing)
├── test_voice_interaction.py      # Voice flow integration tests
├── test_rose_character.py         # Rose's character and therapeutic responses
├── test_memory_therapeutic.py     # Memory system with therapeutic context
├── test_frontend_automated.py     # Automated frontend tests (Playwright)
├── test_frontend_manual.md        # Manual frontend testing checklist
├── test_performance.py            # Performance and load tests
├── test_deployment.py             # Deployment validation tests
└── locustfile.py                  # Load testing configuration
```

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# For frontend automation tests (optional)
pip install playwright pytest-playwright
playwright install

# For load testing (optional)
pip install locust
```

### Run All Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=ai_companion --cov-report=html

# Run specific test file
pytest tests/test_voice_interaction.py -v

# Run specific test class
pytest tests/test_rose_character.py::TestRoseCharacter -v

# Run specific test
pytest tests/test_voice_interaction.py::TestVoiceInteractionFlow::test_complete_voice_flow -v
```

### Run Tests by Category

```bash
# Voice interaction tests
pytest tests/test_voice_interaction.py -v

# Character and therapeutic response tests
pytest tests/test_rose_character.py -v

# Memory system tests
pytest tests/test_memory_therapeutic.py -v

# Performance tests
pytest tests/test_performance.py -v

# Deployment tests
pytest tests/test_deployment.py -v
```

## Test Categories

### 1. Voice Interaction Tests (`test_voice_interaction.py`)

Tests the complete voice interaction flow:
- Audio upload → transcription → processing → response → audio playback
- Session continuity across multiple interactions
- Error recovery and retry mechanisms
- Audio file validation
- STT/TTS error handling

**Key Test Classes:**
- `TestVoiceInteractionFlow`: End-to-end voice flow
- `TestAudioServing`: Audio file serving

**Run:**
```bash
pytest tests/test_voice_interaction.py -v
```

### 2. Rose Character Tests (`test_rose_character.py`)

Tests Rose's healer shaman personality and therapeutic approach:
- Character card contains Rose identity
- Ancient wisdom and holistic approach
- Therapeutic personality traits
- No Ava references remain
- Response length constraints
- Grief counseling scenarios

**Key Test Classes:**
- `TestRoseCharacter`: Character profile validation
- `TestTherapeuticMemoryAnalysis`: Memory prompt validation
- `TestTherapeuticScenarios`: Various counseling scenarios

**Run:**
```bash
pytest tests/test_rose_character.py -v
```

### 3. Memory System Tests (`test_memory_therapeutic.py`)

Tests memory extraction and retrieval with therapeutic context:
- Extraction of emotional states
- Extraction of grief experiences
- Extraction of coping mechanisms
- Extraction of healing goals
- Memory retrieval relevance
- Session continuity

**Key Test Classes:**
- `TestTherapeuticMemoryExtraction`: Memory extraction
- `TestTherapeuticMemoryRetrieval`: Memory retrieval
- `TestMemorySessionContinuity`: Cross-session memory
- `TestMemorySystemIntegration`: Full memory cycle

**Run:**
```bash
pytest tests/test_memory_therapeutic.py -v
```

### 4. Frontend Tests

#### Automated Tests (`test_frontend_automated.py`)

Automated browser tests using Playwright (optional):
- Page rendering
- Voice button interaction
- Responsive design
- Microphone permissions
- Error handling
- Accessibility

**Note:** Playwright tests are commented out by default. Uncomment when ready to run.

**Setup:**
```bash
pip install playwright pytest-playwright
playwright install
```

**Run:**
```bash
# Start server first
uvicorn ai_companion.interfaces.web.app:app --reload

# In another terminal
pytest tests/test_frontend_automated.py -v --headed
```

#### Manual Tests (`test_frontend_manual.md`)

Comprehensive manual testing checklist for:
- Multiple devices (desktop, mobile, tablet)
- Multiple browsers (Chrome, Firefox, Safari, iOS Safari, Android Chrome)
- Responsive design
- Microphone permissions
- Touch interactions
- Accessibility
- Performance

**Use:** Follow the checklist in `test_frontend_manual.md`

### 5. Performance Tests (`test_performance.py`)

Tests system performance and resource usage:
- API response times
- Concurrent session handling
- Resource consumption
- Memory cleanup
- Load scenarios
- Railway platform limits

**Key Test Classes:**
- `TestAPIPerformance`: Response time tests
- `TestConcurrentSessions`: Concurrent load
- `TestResourceConsumption`: Resource limits
- `TestRailwayLimits`: Platform-specific limits
- `TestLoadScenarios`: Various load patterns

**Run:**
```bash
pytest tests/test_performance.py -v
```

### 6. Load Testing (`locustfile.py`)

Comprehensive load testing with Locust:
- Simulates multiple concurrent users
- Tests sustained load
- Tests burst load
- Monitors response times and error rates

**Setup:**
```bash
pip install locust
```

**Run:**
```bash
# Start server
uvicorn ai_companion.interfaces.web.app:app

# In another terminal, run Locust
locust -f tests/locustfile.py --host=http://localhost:8080

# Open browser to http://localhost:8089
# Configure users and spawn rate, then start test
```

**Recommended Scenarios:**
1. Baseline: 5 users, 1/sec spawn, 5 min
2. Normal: 20 users, 2/sec spawn, 10 min
3. Peak: 50 users, 5/sec spawn, 10 min
4. Stress: 100 users, 10/sec spawn, 5 min

### 7. Deployment Tests (`test_deployment.py`)

Tests deployment configuration and production readiness:
- Environment variable configuration
- Health check endpoint
- Railway configuration files
- Database connections
- API endpoint registration
- Deployed instance validation

**Run Locally:**
```bash
pytest tests/test_deployment.py -v
```

**Run Against Deployed Instance:**
```bash
# Set Railway URL
export RAILWAY_URL=https://your-app.railway.app

# Run deployment tests
pytest tests/test_deployment.py::TestDeployedInstance -v
```

## Test Coverage

Generate test coverage report:

```bash
# Run tests with coverage
pytest tests/ --cov=ai_companion --cov-report=html --cov-report=term

# Open coverage report
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Continuous Integration

### GitHub Actions (Example)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Run tests
        run: pytest tests/ -v --cov=ai_companion
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Testing Best Practices

### 1. Test Isolation
- Each test should be independent
- Use fixtures for setup/teardown
- Mock external services (Groq, ElevenLabs, Qdrant)

### 2. Test Data
- Use realistic test data
- Don't use production API keys in tests
- Clean up test data after tests

### 3. Mocking
- Mock external API calls to avoid costs
- Mock slow operations for faster tests
- Use `unittest.mock` or `pytest-mock`

### 4. Assertions
- Use descriptive assertion messages
- Test both success and failure cases
- Verify error messages are user-friendly

### 5. Performance
- Keep unit tests fast (< 1 second each)
- Use markers for slow tests: `@pytest.mark.slow`
- Run slow tests separately in CI

## Troubleshooting

### Tests Fail with Import Errors

```bash
# Install package in development mode
pip install -e .

# Or use uv
uv pip install -e .
```

### Tests Fail with Missing Dependencies

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# Or install all dependencies
uv sync
```

### Playwright Tests Don't Run

```bash
# Install Playwright
pip install playwright pytest-playwright
playwright install

# If still failing, try
playwright install --with-deps
```

### Load Tests Show High Error Rates

- Check if server is running
- Verify API keys are valid
- Check rate limits on external APIs
- Reduce number of concurrent users
- Increase wait time between requests

### Deployment Tests Fail

- Verify RAILWAY_URL is set correctly
- Check if deployed instance is running
- Verify environment variables are set in Railway
- Check Railway logs for errors

## Test Maintenance

### Adding New Tests

1. Create test file in `tests/` directory
2. Follow naming convention: `test_*.py`
3. Use descriptive test names
4. Add docstrings to test classes and methods
5. Update this README with new test information

### Updating Existing Tests

1. Keep tests in sync with code changes
2. Update mocks when API contracts change
3. Add tests for new features
4. Remove tests for deprecated features

### Test Review Checklist

- [ ] Tests are independent and isolated
- [ ] External services are mocked
- [ ] Test data is realistic
- [ ] Both success and failure cases tested
- [ ] Error messages are verified
- [ ] Performance is acceptable
- [ ] Documentation is updated

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Documentation](https://playwright.dev/python/)
- [Locust Documentation](https://docs.locust.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Railway Documentation](https://docs.railway.app/)

## Support

For questions or issues with tests:
1. Check test output for error messages
2. Review this documentation
3. Check individual test file docstrings
4. Review the spec documents in `.kiro/specs/rose-transformation/`
