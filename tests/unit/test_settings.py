"""Unit tests for settings validation."""

import pytest
from pydantic import ValidationError

from ai_companion.settings import Settings


# Shared base kwargs for constructing a valid Settings instance
_BASE_SETTINGS = {
    "GROQ_API_KEY": "test",
    "ELEVENLABS_API_KEY": "test",
    "ELEVENLABS_VOICE_ID": "test",
    "QDRANT_URL": "http://localhost:6333",
}


class TestRangeValidators:
    """Test range validators for numeric configuration values."""

    def test_memory_top_k_valid_range(self):
        """Test MEMORY_TOP_K accepts values within 1-20 range."""
        settings = Settings(**_BASE_SETTINGS, MEMORY_TOP_K=1)
        assert settings.MEMORY_TOP_K == 1

        settings = Settings(**_BASE_SETTINGS, MEMORY_TOP_K=20)
        assert settings.MEMORY_TOP_K == 20

        settings = Settings(**_BASE_SETTINGS, MEMORY_TOP_K=10)
        assert settings.MEMORY_TOP_K == 10

    def test_memory_top_k_invalid_range(self):
        """Test MEMORY_TOP_K rejects values outside 1-20 range."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(**_BASE_SETTINGS, MEMORY_TOP_K=0)
        assert "MEMORY_TOP_K must be between 1 and 20" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            Settings(**_BASE_SETTINGS, MEMORY_TOP_K=21)
        assert "MEMORY_TOP_K must be between 1 and 20" in str(exc_info.value)

    def test_circuit_breaker_threshold_valid_range(self):
        """Test CIRCUIT_BREAKER_FAILURE_THRESHOLD accepts values within 1-10 range."""
        settings = Settings(**_BASE_SETTINGS, CIRCUIT_BREAKER_FAILURE_THRESHOLD=5)
        assert settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD == 5

    def test_circuit_breaker_threshold_invalid_range(self):
        """Test CIRCUIT_BREAKER_FAILURE_THRESHOLD rejects values outside 1-10 range."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(**_BASE_SETTINGS, CIRCUIT_BREAKER_FAILURE_THRESHOLD=0)
        assert "CIRCUIT_BREAKER_FAILURE_THRESHOLD must be between 1 and 10" in str(exc_info.value)

    def test_llm_temperature_valid_range(self):
        """Test LLM temperature values accept 0.0-1.0 range."""
        settings = Settings(
            **_BASE_SETTINGS,
            LLM_TEMPERATURE_DEFAULT=0.7,
            LLM_TEMPERATURE_MEMORY=0.1,
        )
        assert settings.LLM_TEMPERATURE_DEFAULT == 0.7
        assert settings.LLM_TEMPERATURE_MEMORY == 0.1

    def test_llm_temperature_invalid_range(self):
        """Test LLM temperature values reject values outside 0.0-1.0 range."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(**_BASE_SETTINGS, LLM_TEMPERATURE_DEFAULT=1.5)
        assert "LLM_TEMPERATURE_DEFAULT must be between 0.0 and 1.0" in str(exc_info.value)

    def test_timeout_values_positive(self):
        """Test timeout values must be positive."""
        settings = Settings(
            **_BASE_SETTINGS,
            WORKFLOW_TIMEOUT_SECONDS=60,
            LLM_TIMEOUT_SECONDS=30.0,
        )
        assert settings.WORKFLOW_TIMEOUT_SECONDS == 60
        assert settings.LLM_TIMEOUT_SECONDS == 30.0

    def test_timeout_values_reject_zero_or_negative(self):
        """Test timeout values reject zero or negative numbers."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(**_BASE_SETTINGS, WORKFLOW_TIMEOUT_SECONDS=0)
        assert "WORKFLOW_TIMEOUT_SECONDS must be a positive number" in str(exc_info.value)


class TestCrossFieldValidation:
    """Test cross-field validation for related settings."""

    def test_sentry_warning_in_production_without_dsn(self):
        """Test warning is issued when running in production without SENTRY_DSN."""
        with pytest.warns(UserWarning, match="Running in production environment without SENTRY_DSN"):
            Settings(
                **_BASE_SETTINGS,
                ENVIRONMENT="production",
                SENTRY_DSN=None,
            )
