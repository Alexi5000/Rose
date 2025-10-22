"""Unit tests for settings validation."""

import pytest
from pydantic import ValidationError

from ai_companion.settings import Settings


class TestRangeValidators:
    """Test range validators for numeric configuration values."""

    def test_memory_top_k_valid_range(self):
        """Test MEMORY_TOP_K accepts values within 1-20 range."""
        # Test minimum valid value
        settings = Settings(
            GROQ_API_KEY="test",
            ELEVENLABS_API_KEY="test",
            ELEVENLABS_VOICE_ID="test",
            TOGETHER_API_KEY="test",
            QDRANT_URL="http://localhost:6333",
            MEMORY_TOP_K=1,
        )
        assert settings.MEMORY_TOP_K == 1

        # Test maximum valid value
        settings = Settings(
            GROQ_API_KEY="test",
            ELEVENLABS_API_KEY="test",
            ELEVENLABS_VOICE_ID="test",
            TOGETHER_API_KEY="test",
            QDRANT_URL="http://localhost:6333",
            MEMORY_TOP_K=20,
        )
        assert settings.MEMORY_TOP_K == 20

        # Test middle value
        settings = Settings(
            GROQ_API_KEY="test",
            ELEVENLABS_API_KEY="test",
            ELEVENLABS_VOICE_ID="test",
            TOGETHER_API_KEY="test",
            QDRANT_URL="http://localhost:6333",
            MEMORY_TOP_K=10,
        )
        assert settings.MEMORY_TOP_K == 10

    def test_memory_top_k_invalid_range(self):
        """Test MEMORY_TOP_K rejects values outside 1-20 range."""
        # Test below minimum
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                GROQ_API_KEY="test",
                ELEVENLABS_API_KEY="test",
                ELEVENLABS_VOICE_ID="test",
                TOGETHER_API_KEY="test",
                QDRANT_URL="http://localhost:6333",
                MEMORY_TOP_K=0,
            )
        assert "MEMORY_TOP_K must be between 1 and 20" in str(exc_info.value)

        # Test above maximum
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                GROQ_API_KEY="test",
                ELEVENLABS_API_KEY="test",
                ELEVENLABS_VOICE_ID="test",
                TOGETHER_API_KEY="test",
                QDRANT_URL="http://localhost:6333",
                MEMORY_TOP_K=21,
            )
        assert "MEMORY_TOP_K must be between 1 and 20" in str(exc_info.value)

    def test_circuit_breaker_threshold_valid_range(self):
        """Test CIRCUIT_BREAKER_FAILURE_THRESHOLD accepts values within 1-10 range."""
        settings = Settings(
            GROQ_API_KEY="test",
            ELEVENLABS_API_KEY="test",
            ELEVENLABS_VOICE_ID="test",
            TOGETHER_API_KEY="test",
            QDRANT_URL="http://localhost:6333",
            CIRCUIT_BREAKER_FAILURE_THRESHOLD=5,
        )
        assert settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD == 5

    def test_circuit_breaker_threshold_invalid_range(self):
        """Test CIRCUIT_BREAKER_FAILURE_THRESHOLD rejects values outside 1-10 range."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                GROQ_API_KEY="test",
                ELEVENLABS_API_KEY="test",
                ELEVENLABS_VOICE_ID="test",
                TOGETHER_API_KEY="test",
                QDRANT_URL="http://localhost:6333",
                CIRCUIT_BREAKER_FAILURE_THRESHOLD=0,
            )
        assert "CIRCUIT_BREAKER_FAILURE_THRESHOLD must be between 1 and 10" in str(exc_info.value)

    def test_llm_temperature_valid_range(self):
        """Test LLM temperature values accept 0.0-1.0 range."""
        settings = Settings(
            GROQ_API_KEY="test",
            ELEVENLABS_API_KEY="test",
            ELEVENLABS_VOICE_ID="test",
            TOGETHER_API_KEY="test",
            QDRANT_URL="http://localhost:6333",
            LLM_TEMPERATURE_DEFAULT=0.7,
            LLM_TEMPERATURE_ROUTER=0.3,
            LLM_TEMPERATURE_MEMORY=0.1,
        )
        assert settings.LLM_TEMPERATURE_DEFAULT == 0.7
        assert settings.LLM_TEMPERATURE_ROUTER == 0.3
        assert settings.LLM_TEMPERATURE_MEMORY == 0.1

    def test_llm_temperature_invalid_range(self):
        """Test LLM temperature values reject values outside 0.0-1.0 range."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                GROQ_API_KEY="test",
                ELEVENLABS_API_KEY="test",
                ELEVENLABS_VOICE_ID="test",
                TOGETHER_API_KEY="test",
                QDRANT_URL="http://localhost:6333",
                LLM_TEMPERATURE_DEFAULT=1.5,
            )
        assert "LLM_TEMPERATURE_DEFAULT must be between 0.0 and 1.0" in str(exc_info.value)

    def test_timeout_values_positive(self):
        """Test timeout values must be positive."""
        settings = Settings(
            GROQ_API_KEY="test",
            ELEVENLABS_API_KEY="test",
            ELEVENLABS_VOICE_ID="test",
            TOGETHER_API_KEY="test",
            QDRANT_URL="http://localhost:6333",
            WORKFLOW_TIMEOUT_SECONDS=60,
            LLM_TIMEOUT_SECONDS=30.0,
        )
        assert settings.WORKFLOW_TIMEOUT_SECONDS == 60
        assert settings.LLM_TIMEOUT_SECONDS == 30.0

    def test_timeout_values_reject_zero_or_negative(self):
        """Test timeout values reject zero or negative numbers."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                GROQ_API_KEY="test",
                ELEVENLABS_API_KEY="test",
                ELEVENLABS_VOICE_ID="test",
                TOGETHER_API_KEY="test",
                QDRANT_URL="http://localhost:6333",
                WORKFLOW_TIMEOUT_SECONDS=0,
            )
        assert "WORKFLOW_TIMEOUT_SECONDS must be a positive number" in str(exc_info.value)


class TestCrossFieldValidation:
    """Test cross-field validation for related settings."""

    def test_postgresql_requires_database_url(self):
        """Test DATABASE_URL is required when using PostgreSQL."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                GROQ_API_KEY="test",
                ELEVENLABS_API_KEY="test",
                ELEVENLABS_VOICE_ID="test",
                TOGETHER_API_KEY="test",
                QDRANT_URL="http://localhost:6333",
                FEATURE_DATABASE_TYPE="postgresql",
                DATABASE_URL=None,
            )
        error_msg = str(exc_info.value)
        assert "DATABASE_URL is required when FEATURE_DATABASE_TYPE is 'postgresql'" in error_msg
        assert "postgresql://user:password@localhost:5432/dbname" in error_msg

    def test_postgresql_with_database_url_succeeds(self):
        """Test PostgreSQL configuration succeeds with DATABASE_URL."""
        settings = Settings(
            GROQ_API_KEY="test",
            ELEVENLABS_API_KEY="test",
            ELEVENLABS_VOICE_ID="test",
            TOGETHER_API_KEY="test",
            QDRANT_URL="http://localhost:6333",
            FEATURE_DATABASE_TYPE="postgresql",
            DATABASE_URL="postgresql://user:pass@localhost:5432/db",
        )
        assert settings.FEATURE_DATABASE_TYPE == "postgresql"
        assert settings.DATABASE_URL == "postgresql://user:pass@localhost:5432/db"

    def test_whatsapp_enabled_requires_all_fields(self):
        """Test WhatsApp fields are required when FEATURE_WHATSAPP_ENABLED is true."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                GROQ_API_KEY="test",
                ELEVENLABS_API_KEY="test",
                ELEVENLABS_VOICE_ID="test",
                TOGETHER_API_KEY="test",
                QDRANT_URL="http://localhost:6333",
                FEATURE_WHATSAPP_ENABLED=True,
                WHATSAPP_PHONE_NUMBER_ID=None,
                WHATSAPP_TOKEN=None,
                WHATSAPP_VERIFY_TOKEN=None,
            )
        error_msg = str(exc_info.value)
        assert "WhatsApp integration is enabled" in error_msg
        assert "WHATSAPP_PHONE_NUMBER_ID" in error_msg
        assert "WHATSAPP_TOKEN" in error_msg
        assert "WHATSAPP_VERIFY_TOKEN" in error_msg

    def test_whatsapp_enabled_with_all_fields_succeeds(self):
        """Test WhatsApp configuration succeeds with all required fields."""
        settings = Settings(
            GROQ_API_KEY="test",
            ELEVENLABS_API_KEY="test",
            ELEVENLABS_VOICE_ID="test",
            TOGETHER_API_KEY="test",
            QDRANT_URL="http://localhost:6333",
            FEATURE_WHATSAPP_ENABLED=True,
            WHATSAPP_PHONE_NUMBER_ID="123456",
            WHATSAPP_TOKEN="token123",
            WHATSAPP_VERIFY_TOKEN="verify123",
        )
        assert settings.FEATURE_WHATSAPP_ENABLED is True
        assert settings.WHATSAPP_PHONE_NUMBER_ID == "123456"

    def test_whatsapp_disabled_does_not_require_fields(self):
        """Test WhatsApp fields are not required when disabled."""
        settings = Settings(
            GROQ_API_KEY="test",
            ELEVENLABS_API_KEY="test",
            ELEVENLABS_VOICE_ID="test",
            TOGETHER_API_KEY="test",
            QDRANT_URL="http://localhost:6333",
            FEATURE_WHATSAPP_ENABLED=False,
        )
        assert settings.FEATURE_WHATSAPP_ENABLED is False

    def test_sentry_warning_in_production_without_dsn(self):
        """Test warning is issued when running in production without SENTRY_DSN."""
        with pytest.warns(UserWarning, match="Running in production environment without SENTRY_DSN"):
            Settings(
                GROQ_API_KEY="test",
                ELEVENLABS_API_KEY="test",
                ELEVENLABS_VOICE_ID="test",
                TOGETHER_API_KEY="test",
                QDRANT_URL="http://localhost:6333",
                ENVIRONMENT="production",
                SENTRY_DSN=None,
            )
