"""Application settings and configuration management.

This module defines all configuration settings for the Rose the Healer Shaman
application using Pydantic Settings. Settings are loaded from environment
variables with validation and type checking.

All settings can be configured via:
- Environment variables
- .env file in the project root
- Default values defined in this module

Example:
    Load settings in your module:

    >>> from ai_companion.settings import settings
    >>> print(settings.GROQ_API_KEY)

Note:
    Only MVP-active settings belong here. Frozen features (WhatsApp, image
    generation, PostgreSQL, multi-region) have been removed per tree-shaking.
"""

import sys
from typing import Any

from pydantic import ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from ai_companion.config.server_config import (
    AUDIO_CLEANUP_MAX_AGE_HOURS,
    MAX_REQUEST_SIZE_BYTES,
    RATE_LIMIT_REQUESTS_PER_MINUTE,
    WEB_SERVER_HOST,
    WEB_SERVER_PORT,
    WORKFLOW_TIMEOUT_SECONDS,
)


class Settings(BaseSettings):
    """Application settings with environment variable loading and validation.

    This class defines all configuration parameters for the application,
    including API keys, model names, memory configuration, and server settings.

    Attributes:
        GROQ_API_KEY: API key for Groq services (LLM, STT)
        ELEVENLABS_API_KEY: API key for ElevenLabs TTS
        ELEVENLABS_VOICE_ID: Default voice ID for ElevenLabs
        QDRANT_API_KEY: Optional API key for Qdrant cloud
        QDRANT_URL: URL for Qdrant vector database
        TEXT_MODEL_NAME: Primary LLM model name
        SMALL_TEXT_MODEL_NAME: Smaller/faster LLM model name
        STT_MODEL_NAME: Speech-to-text model name
        TTS_MODEL_NAME: Text-to-speech model name
        MEMORY_TOP_K: Number of memories to retrieve
        WORKFLOW_TIMEOUT_SECONDS: Global workflow execution timeout
        PORT: Server port number
        HOST: Server host address
        ALLOWED_ORIGINS: CORS allowed origins (comma-separated)
        RATE_LIMIT_ENABLED: Enable/disable rate limiting
        LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        LOG_FORMAT: Log output format (json or console)
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_file_encoding="utf-8")

    # Required API keys
    GROQ_API_KEY: str
    ELEVENLABS_API_KEY: str
    ELEVENLABS_VOICE_ID: str

    # Qdrant configuration
    QDRANT_API_KEY: str | None = None
    QDRANT_URL: str
    QDRANT_PORT: str = "6333"
    QDRANT_HOST: str | None = None
    # Qdrant retry/backoff configuration (for transient internal server errors)
    QDRANT_MAX_RETRIES: int = 3
    QDRANT_INITIAL_BACKOFF: float = 0.5
    QDRANT_MAX_BACKOFF: float = 5.0

    # Model configurations
    LLM_PROVIDER: str = "groq"
    LLM_FALLBACK_PROVIDER: str | None = "openrouter"
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL_NAME: str = "openai/gpt-oss-120b"
    OPENROUTER_APP_NAME: str = "Rose"
    TEXT_MODEL_NAME: str = "openai/gpt-oss-120b"
    SMALL_TEXT_MODEL_NAME: str = "openai/gpt-oss-20b"
    STT_PROVIDER: str = "groq"
    STT_MODEL_NAME: str = "whisper-large-v3-turbo"
    DEEPGRAM_API_KEY: str | None = None
    DEEPGRAM_MODEL_NAME: str = "nova-3"
    DEEPGRAM_LANGUAGE: str = "en-US"
    DEEPGRAM_AUDIO_MIMETYPE: str = "audio/webm"
    DEEPGRAM_ENDPOINTING_MS: int = 300
    DEEPGRAM_UTTERANCE_END_MS: int = 1000
    TTS_PROVIDER: str = "elevenlabs"
    TTS_MODEL_NAME: str = "eleven_turbo_v2_5"

    # Memory configuration
    EMBEDDING_PROVIDER: str = "sentence_transformer"
    MEMORY_PROVIDER: str = "long_term"
    MEMORY_TOP_K: int = 5
    TOTAL_MESSAGES_SUMMARY_TRIGGER: int = 30
    TOTAL_MESSAGES_AFTER_SUMMARY: int = 10

    SHORT_TERM_MEMORY_DB_PATH: str = "/app/data/memory.db"

    # Workflow configuration
    WORKFLOW_TIMEOUT_SECONDS: int = WORKFLOW_TIMEOUT_SECONDS  # Global timeout for LangGraph workflow execution

    # Server configuration (for production deployment)
    PORT: int = WEB_SERVER_PORT
    HOST: str = WEB_SERVER_HOST

    # Security configuration
    ALLOWED_ORIGINS: str = ""  # Comma-separated list of allowed origins; must be set explicitly
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = RATE_LIMIT_REQUESTS_PER_MINUTE  # Requests per minute per IP
    ENABLE_SECURITY_HEADERS: bool = True

    # Logging configuration
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "json"  # json or console
    LOG_SENSITIVE_CONTENT: bool = (
        False  # Opt-in only: log transcripts, memory text, or other sensitive content previews
    )

    # API Documentation configuration
    ENABLE_API_DOCS: bool = False  # Enable OpenAPI/Swagger documentation (set True in dev .env)

    # Request size limits (in bytes)
    MAX_REQUEST_SIZE: int = MAX_REQUEST_SIZE_BYTES  # 10MB default

    # Session cleanup configuration
    SESSION_RETENTION_DAYS: int = 7  # Delete sessions older than 7 days

    # Feature Flags
    FEATURE_TTS_CACHE_ENABLED: bool = True  # Enable TTS response caching
    FEATURE_TIMING_METRICS_ENABLED: bool = True  # Include pipeline timing metrics in response

    # Speech-to-text configuration
    STT_MAX_RETRIES: int = 3  # Maximum retry attempts for STT
    STT_INITIAL_BACKOFF: float = 1.0  # Initial backoff in seconds
    STT_MAX_BACKOFF: float = 10.0  # Maximum backoff in seconds
    STT_TIMEOUT: int = 60  # API timeout in seconds
    STT_MAX_AUDIO_SIZE_MB: int = 25  # Maximum audio file size in MB

    # Text-to-speech configuration
    TTS_CACHE_ENABLED: bool = True  # Enable TTS response caching
    TTS_CACHE_TTL_HOURS: int = 24  # Cache time-to-live in hours
    TTS_VOICE_STABILITY: float = (
        0.50  # Voice stability (0.0-1.0); 0.50 = natural conversational variation (retail-blend sweet spot)
    )
    TTS_VOICE_SIMILARITY: float = (
        0.75  # Voice similarity boost (0.0-1.0); 0.75 = consistent fidelity without over-clamping
    )
    TTS_VOICE_STYLE: float = 0.15  # Style exaggeration (0.0-1.0); 0.15 = subtle warmth without over-acting
    TTS_VOICE_SPEED: float = 0.92  # Speech speed multiplier (0.7-1.2); 0.92 = slightly slower for calming delivery
    TTS_OUTPUT_FORMAT: str = "mp3_44100_128"  # ElevenLabs output encoding
    TTS_USE_SPEAKER_BOOST: bool = True  # Enable ElevenLabs speaker boost for warmth
    TTS_LANGUAGE_CODE: str = "en"  # Language code for ElevenLabs language-specific acoustic tuning
    TTS_MAX_TEXT_LENGTH: int = 5000  # Maximum text length for TTS

    # Audio file cleanup configuration
    AUDIO_CLEANUP_MAX_AGE_HOURS: int = AUDIO_CLEANUP_MAX_AGE_HOURS  # Delete audio files older than this

    # Circuit breaker configuration
    # Increased for extended conversations (8+ turns, 120+ seconds)
    # Previous: 5 failures caused issues after 6-7 turns in stress testing
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 10  # Failures before opening circuit (max: 10)
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 90  # Seconds before attempting recovery (increased for longer sessions)

    # LLM timeout and retry configuration
    LLM_TIMEOUT_SECONDS: float = 30.0  # Timeout for LLM API calls
    LLM_MAX_RETRIES: int = 3  # Maximum retry attempts for LLM calls
    LLM_TEMPERATURE_DEFAULT: float = 0.72  # Default temperature for LLM responses - balanced warmth + consistency
    LLM_TEMPERATURE_MEMORY: float = 0.1  # Temperature for memory extraction

    # Safety classification configuration
    SAFETY_PROVIDER: str = "deterministic"

    # Monitoring and alerting configuration
    SENTRY_DSN: str | None = None  # Sentry DSN for error tracking
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1  # Percentage of transactions to trace (0.0-1.0)
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.1  # Percentage of transactions to profile (0.0-1.0)
    ENVIRONMENT: str = "production"  # Environment name (development, staging, production)
    APP_VERSION: str = "1.0.0"  # Application version for tracking

    # Alert configuration
    ALERT_ERROR_RATE_ENABLED: bool = True  # Enable error rate alerts
    ALERT_ERROR_RATE_THRESHOLD: float = 5.0  # Error rate threshold percentage
    ALERT_RESPONSE_TIME_ENABLED: bool = True  # Enable response time alerts
    ALERT_RESPONSE_TIME_THRESHOLD: float = 2000.0  # Response time threshold in ms
    ALERT_MEMORY_ENABLED: bool = True  # Enable memory usage alerts
    ALERT_MEMORY_THRESHOLD: float = 80.0  # Memory usage threshold percentage
    ALERT_CIRCUIT_BREAKER_ENABLED: bool = True  # Enable circuit breaker alerts

    # Monitoring scheduler configuration
    MONITORING_EVALUATION_INTERVAL: int = 60  # Seconds between alert evaluations

    @field_validator("GROQ_API_KEY", "ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID", "QDRANT_URL")
    @classmethod
    def validate_required_fields(cls, v: str, info: Any) -> str:
        """Validate that required fields are not empty.

        Args:
            v: Field value to validate
            info: Field information from Pydantic

        Returns:
            Validated field value

        Raises:
            ValueError: If field is empty or whitespace-only
        """
        if not v or v.strip() == "":
            raise ValueError(f"{info.field_name} is required and cannot be empty")
        return v

    @field_validator("MEMORY_TOP_K")
    @classmethod
    def validate_memory_top_k(cls, v: int) -> int:
        """Validate MEMORY_TOP_K is within acceptable range.

        Args:
            v: Number of memories to retrieve

        Returns:
            Validated MEMORY_TOP_K value

        Raises:
            ValueError: If value is outside the range 1-20
        """
        if v < 1 or v > 20:
            raise ValueError(
                f"MEMORY_TOP_K must be between 1 and 20 (got {v}). "
                "This controls how many relevant memories are retrieved for context."
            )
        return v

    @field_validator("LLM_PROVIDER")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        """Validate the primary LLM provider selector."""

        provider = v.strip().lower()
        if provider not in {"groq", "openrouter"}:
            raise ValueError("LLM_PROVIDER must be one of: groq, openrouter")
        return provider

    @field_validator("LLM_FALLBACK_PROVIDER", mode="before")
    @classmethod
    def normalize_optional_provider(cls, v: Any) -> str | None:
        """Treat empty optional provider env vars as disabled."""

        if v is None:
            return None
        provider = str(v).strip().lower()
        return provider or None

    @field_validator("LLM_FALLBACK_PROVIDER")
    @classmethod
    def validate_llm_fallback_provider(cls, v: str | None) -> str | None:
        """Validate the optional LLM fallback provider selector."""

        if v is not None and v not in {"groq", "openrouter"}:
            raise ValueError("LLM_FALLBACK_PROVIDER must be empty or one of: groq, openrouter")
        return v

    @field_validator("STT_PROVIDER")
    @classmethod
    def validate_stt_provider(cls, v: str) -> str:
        """Validate the speech-to-text provider selector."""

        provider = v.strip().lower()
        if provider not in {"groq", "deepgram", "deepgram_streaming"}:
            raise ValueError("STT_PROVIDER must be one of: groq, deepgram, deepgram_streaming")
        return provider

    @field_validator("DEEPGRAM_ENDPOINTING_MS", "DEEPGRAM_UTTERANCE_END_MS")
    @classmethod
    def validate_deepgram_timing_ms(cls, v: int, info: Any) -> int:
        """Validate Deepgram streaming timing controls."""

        if v <= 0:
            raise ValueError(f"{info.field_name} must be a positive integer in milliseconds")
        return v

    @field_validator("TTS_PROVIDER")
    @classmethod
    def validate_tts_provider(cls, v: str) -> str:
        """Validate the text-to-speech provider selector."""

        provider = v.strip().lower()
        if provider not in {"elevenlabs", "elevenlabs_tts", "text_only", "text_only_tts", "browser_speech"}:
            raise ValueError(
                "TTS_PROVIDER must be one of: elevenlabs, elevenlabs_tts, text_only, text_only_tts, browser_speech"
            )
        return provider

    @field_validator("EMBEDDING_PROVIDER")
    @classmethod
    def validate_embedding_provider(cls, v: str) -> str:
        """Validate the embedding provider selector."""

        provider = v.strip().lower()
        if provider not in {"sentence_transformer", "sentence-transformer", "local"}:
            raise ValueError("EMBEDDING_PROVIDER must be one of: sentence_transformer, sentence-transformer, local")
        return provider

    @field_validator("MEMORY_PROVIDER")
    @classmethod
    def validate_memory_provider(cls, v: str) -> str:
        """Validate the memory provider selector."""

        provider = v.strip().lower()
        if provider not in {"long_term", "long_term_memory", "qdrant"}:
            raise ValueError("MEMORY_PROVIDER must be one of: long_term, long_term_memory, qdrant")
        return provider

    @field_validator("SAFETY_PROVIDER")
    @classmethod
    def validate_safety_provider(cls, v: str) -> str:
        """Validate the safety classifier provider selector."""

        provider = v.strip().lower()
        if provider not in {"deterministic", "deterministic_crisis", "local"}:
            raise ValueError("SAFETY_PROVIDER must be one of: deterministic, deterministic_crisis, local")
        return provider

    @field_validator("CIRCUIT_BREAKER_FAILURE_THRESHOLD")
    @classmethod
    def validate_circuit_breaker_threshold(cls, v: int) -> int:
        """Validate circuit breaker failure threshold is within acceptable range.

        Args:
            v: Number of failures before opening circuit

        Returns:
            Validated threshold value

        Raises:
            ValueError: If value is outside the range 1-10
        """
        if v < 1 or v > 10:
            raise ValueError(
                f"CIRCUIT_BREAKER_FAILURE_THRESHOLD must be between 1 and 10 (got {v}). "
                "Lower values make the circuit breaker more sensitive to failures."
            )
        return v

    @field_validator(
        "LLM_TEMPERATURE_DEFAULT",
        "LLM_TEMPERATURE_MEMORY",
        "TTS_VOICE_STABILITY",
        "TTS_VOICE_SIMILARITY",
        "TTS_VOICE_STYLE",
        "SENTRY_TRACES_SAMPLE_RATE",
        "SENTRY_PROFILES_SAMPLE_RATE",
    )
    @classmethod
    def validate_temperature_and_rates(cls, v: float, info: Any) -> float:
        """Validate temperature and rate values are within 0.0-1.0 range.

        Args:
            v: Temperature or rate value
            info: Field information from Pydantic

        Returns:
            Validated value

        Raises:
            ValueError: If value is outside the range 0.0-1.0
        """
        if v < 0.0 or v > 1.0:
            raise ValueError(
                f"{info.field_name} must be between 0.0 and 1.0 (got {v}). "
                "This controls randomness/sampling for the respective feature."
            )
        return v

    @field_validator(
        "WORKFLOW_TIMEOUT_SECONDS",
        "STT_TIMEOUT",
        "CIRCUIT_BREAKER_RECOVERY_TIMEOUT",
        "LLM_TIMEOUT_SECONDS",
    )
    @classmethod
    def validate_timeout_values(cls, v: float | int, info: Any) -> float | int:
        """Validate timeout values are positive numbers.

        Args:
            v: Timeout value in seconds
            info: Field information from Pydantic

        Returns:
            Validated timeout value

        Raises:
            ValueError: If value is not positive
        """
        if v <= 0:
            raise ValueError(
                f"{info.field_name} must be a positive number (got {v}). Timeout values must be greater than 0 seconds."
            )
        return v

    @model_validator(mode="after")
    def validate_cross_field_dependencies(self) -> "Settings":
        """Validate cross-field dependencies and provide detailed error messages.

        Returns:
            Validated Settings instance

        Raises:
            ValueError: If related settings are inconsistent
        """
        # Validate Sentry configuration when monitoring is enabled
        if self.ENVIRONMENT in ["staging", "production"] and not self.SENTRY_DSN:
            # This is a warning case - we log but don't fail
            import warnings

            warnings.warn(
                f"Running in {self.ENVIRONMENT} environment without SENTRY_DSN configured. "
                "Error tracking and monitoring will be limited. "
                "Consider setting SENTRY_DSN in your .env file for better observability.",
                UserWarning,
            )

        return self

    def get_allowed_origins(self) -> list[str]:
        """Parse ALLOWED_ORIGINS into a list of origin URLs.

        Returns:
            List of allowed origin URLs, or ["*"] for all origins

        Example:
            >>> settings.ALLOWED_ORIGINS = "http://localhost:3000,https://example.com"
            >>> settings.get_allowed_origins()
            ['http://localhost:3000', 'https://example.com']
        """
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    def validate_connectivity(self) -> None:
        """Validate connectivity to external services at startup.

        This method performs optional connectivity checks to Qdrant and database
        services. Warnings are logged for connectivity issues, but startup is
        not blocked to allow the application to start in degraded mode.

        Note:
            This method should be called after settings are loaded but before
            the application starts accepting requests.
        """
        import logging

        logger = logging.getLogger(__name__)

        # Validate Qdrant connectivity
        try:
            from qdrant_client import QdrantClient

            client = QdrantClient(url=self.QDRANT_URL, api_key=self.QDRANT_API_KEY, timeout=5)
            # Try to get collections to verify connectivity
            client.get_collections()
            logger.info("Qdrant connectivity validated successfully")
        except Exception as e:
            logger.warning(
                f"Qdrant connectivity check failed: {e}. "
                f"Memory features may not work correctly. "
                f"Please verify QDRANT_URL ({self.QDRANT_URL}) is accessible and QDRANT_API_KEY is valid."
            )

        logger.info("Using SQLite database (no connectivity check needed)")


def load_settings() -> Settings:
    """Load and validate settings with helpful error messages.

    This function loads settings from environment variables and the .env file,
    validates all required fields, and provides clear error messages if
    configuration is missing or invalid.

    Returns:
        Validated Settings instance

    Raises:
        SystemExit: If required settings are missing or invalid

    Example:
        >>> settings = load_settings()
        >>> settings.TEXT_MODEL_NAME
        'openai/gpt-oss-120b'
    """
    try:
        return Settings()  # type: ignore[call-arg]  # Pydantic BaseSettings loads from environment variables
    except ValidationError as e:
        sys.stderr.write("Configuration error: missing or invalid environment variables\n")
        sys.stderr.write("\nPlease ensure the following environment variables are set:\n")
        for error in e.errors():
            field = error["loc"][0]
            msg = error["msg"]
            sys.stderr.write(f"  - {field}: {msg}\n")
        sys.stderr.write("\nRefer to .env.example for required variables.\n")
        sys.exit(1)


# Global settings instance - import this in other modules
settings = load_settings()
