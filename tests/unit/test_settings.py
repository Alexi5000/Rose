"""Unit tests for settings validation."""

from pathlib import Path

import pytest
from pydantic import ValidationError

import ai_companion.settings as settings_module
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

    @pytest.mark.parametrize("field_name", ["DEEPGRAM_ENDPOINTING_MS", "DEEPGRAM_UTTERANCE_END_MS"])
    def test_deepgram_streaming_timing_values_reject_zero_or_negative(self, field_name):
        """Test Deepgram streaming timing knobs reject invalid millisecond values."""

        with pytest.raises(ValidationError) as exc_info:
            Settings(**_BASE_SETTINGS, **{field_name: 0})

        assert f"{field_name} must be a positive integer in milliseconds" in str(exc_info.value)


class TestProviderSettings:
    """Test provider configuration defaults."""

    def test_llm_provider_defaults_keep_groq_primary(self):
        settings = Settings(**_BASE_SETTINGS)

        assert settings.LLM_PROVIDER == "groq"
        assert settings.LLM_FALLBACK_PROVIDER == "openrouter"
        assert settings.OPENROUTER_API_KEY is None
        assert settings.OPENROUTER_BASE_URL == "https://openrouter.ai/api/v1"
        assert settings.STT_PROVIDER == "groq"
        assert settings.DEEPGRAM_API_KEY is None
        assert settings.DEEPGRAM_MODEL_NAME == "nova-3"
        assert settings.DEEPGRAM_LANGUAGE == "en-US"
        assert settings.DEEPGRAM_ENDPOINTING_MS == 300
        assert settings.DEEPGRAM_UTTERANCE_END_MS == 1000
        assert settings.LOG_SENSITIVE_CONTENT is False

    def test_provider_selectors_accept_supported_aliases(self):
        settings = Settings(
            **_BASE_SETTINGS,
            LLM_PROVIDER="openrouter",
            LLM_FALLBACK_PROVIDER="",
            STT_PROVIDER="deepgram_streaming",
            TTS_PROVIDER="browser_speech",
            EMBEDDING_PROVIDER="local",
            MEMORY_PROVIDER="qdrant",
            SAFETY_PROVIDER="deterministic_crisis",
        )

        assert settings.LLM_PROVIDER == "openrouter"
        assert settings.LLM_FALLBACK_PROVIDER is None
        assert settings.STT_PROVIDER == "deepgram_streaming"
        assert settings.TTS_PROVIDER == "browser_speech"
        assert settings.EMBEDDING_PROVIDER == "local"
        assert settings.MEMORY_PROVIDER == "qdrant"
        assert settings.SAFETY_PROVIDER == "deterministic_crisis"

    @pytest.mark.parametrize(
        ("field_name", "message"),
        [
            ("LLM_PROVIDER", "LLM_PROVIDER must be one of"),
            ("LLM_FALLBACK_PROVIDER", "LLM_FALLBACK_PROVIDER must be empty or one of"),
            ("STT_PROVIDER", "STT_PROVIDER must be one of"),
            ("TTS_PROVIDER", "TTS_PROVIDER must be one of"),
            ("EMBEDDING_PROVIDER", "EMBEDDING_PROVIDER must be one of"),
            ("MEMORY_PROVIDER", "MEMORY_PROVIDER must be one of"),
            ("SAFETY_PROVIDER", "SAFETY_PROVIDER must be one of"),
        ],
    )
    def test_provider_selectors_reject_unknown_values(self, field_name, message):
        with pytest.raises(ValidationError) as exc_info:
            Settings(**_BASE_SETTINGS, **{field_name: "unknown"})

        assert message in str(exc_info.value)


class TestSettingsTextQuality:
    """Guard active startup/configuration messages against mojibake."""

    def test_settings_source_runtime_text_is_ascii(self):
        text = Path(settings_module.__file__).read_text(encoding="utf-8")

        assert text.isascii()
        assert "Configuration error: missing or invalid environment variables" in text
        assert "Qdrant connectivity validated successfully" in text
        assert "Qdrant connectivity check failed" in text


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
