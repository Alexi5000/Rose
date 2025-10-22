"""Pytest configuration and shared fixtures.

This module configures pytest and imports all fixtures from the fixtures directory
to make them available across all test modules.
"""

import os
import sys
from pathlib import Path

import pytest

# Set test environment variables BEFORE any imports
# This prevents settings validation errors during test collection
os.environ.setdefault("GROQ_API_KEY", "test_groq_key")
os.environ.setdefault("ELEVENLABS_API_KEY", "test_elevenlabs_key")
os.environ.setdefault("ELEVENLABS_VOICE_ID", "test_voice_id")
os.environ.setdefault("TOGETHER_API_KEY", "test_together_key")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("QDRANT_API_KEY", "test_qdrant_key")

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import all fixtures to make them available to all tests
# Pytest will automatically discover fixtures in conftest.py
# We don't need to explicitly import them here - just define them or
# import the modules so pytest can discover them
pytest_plugins = [
    "tests.fixtures.mock_clients",
    "tests.fixtures.audio_samples",
    "tests.fixtures.mock_responses",
    "tests.fixtures.sample_audio",
    "tests.fixtures.sample_data",
]


# Pytest configuration hooks
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


@pytest.fixture(scope="session")
def test_settings():
    """Provide test-specific settings that override production settings.

    Returns:
        dict: Test configuration overrides
    """
    return {
        "GROQ_API_KEY": "test_groq_key",
        "ELEVENLABS_API_KEY": "test_elevenlabs_key",
        "ELEVENLABS_VOICE_ID": "test_voice_id",
        "TOGETHER_API_KEY": "test_together_key",
        "QDRANT_URL": "http://localhost:6333",
        "QDRANT_API_KEY": "test_qdrant_key",
        "TEXT_MODEL_NAME": "llama-3.3-70b-versatile",
        "STT_MODEL_NAME": "whisper-large-v3",
        "TTS_MODEL_NAME": "eleven_flash_v2_5",
        "MEMORY_TOP_K": 3,
        "WORKFLOW_TIMEOUT_SECONDS": 60,
        "TTS_CACHE_ENABLED": True,
        "CIRCUIT_BREAKER_FAILURE_THRESHOLD": 5,
        "CIRCUIT_BREAKER_RECOVERY_TIMEOUT": 60,
    }


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests to ensure test isolation.

    This fixture runs automatically before each test to prevent state leakage
    between tests when using singleton patterns.
    """
    # Clear any cached module instances
    # This will be expanded as we identify singleton patterns in the codebase
    yield
    # Cleanup after test
    pass


@pytest.fixture
def mock_env_vars(monkeypatch, test_settings):
    """Mock environment variables for testing.

    Args:
        monkeypatch: Pytest monkeypatch fixture
        test_settings: Test settings fixture
    """
    for key, value in test_settings.items():
        monkeypatch.setenv(key, str(value))
