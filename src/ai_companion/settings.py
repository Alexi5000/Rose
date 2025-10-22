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
"""

import sys
from typing import Any

from pydantic import ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable loading and validation.

    This class defines all configuration parameters for the application,
    including API keys, model names, memory configuration, and server settings.

    Attributes:
        GROQ_API_KEY: API key for Groq services (LLM, STT)
        ELEVENLABS_API_KEY: API key for ElevenLabs TTS
        ELEVENLABS_VOICE_ID: Default voice ID for ElevenLabs
        TOGETHER_API_KEY: API key for Together AI image generation
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
    TOGETHER_API_KEY: str

    # Qdrant configuration
    QDRANT_API_KEY: str | None = None
    QDRANT_URL: str
    QDRANT_PORT: str = "6333"
    QDRANT_HOST: str | None = None

    # Model configurations
    TEXT_MODEL_NAME: str = "llama-3.3-70b-versatile"
    SMALL_TEXT_MODEL_NAME: str = "llama-3.1-8b-instant"
    STT_MODEL_NAME: str = "whisper-large-v3"
    TTS_MODEL_NAME: str = "eleven_flash_v2_5"
    TTI_MODEL_NAME: str = "black-forest-labs/FLUX.1-schnell-Free"
    ITT_MODEL_NAME: str = "llama-3.2-90b-vision-preview"

    # Rose-specific configuration
    ROSE_VOICE_ID: str | None = None  # Optional: Override ELEVENLABS_VOICE_ID for Rose's specific voice

    # WhatsApp integration (optional - frozen for future release)
    WHATSAPP_PHONE_NUMBER_ID: str | None = None
    WHATSAPP_TOKEN: str | None = None
    WHATSAPP_VERIFY_TOKEN: str | None = None

    # Memory configuration
    MEMORY_TOP_K: int = 3
    ROUTER_MESSAGES_TO_ANALYZE: int = 3
    TOTAL_MESSAGES_SUMMARY_TRIGGER: int = 20
    TOTAL_MESSAGES_AFTER_SUMMARY: int = 5

    SHORT_TERM_MEMORY_DB_PATH: str = "/app/data/memory.db"

    # Workflow configuration
    WORKFLOW_TIMEOUT_SECONDS: int = 60  # Global timeout for LangGraph workflow execution

    # Server configuration (for production deployment)
    PORT: int = 8080
    HOST: str = "0.0.0.0"

    # Security configuration
    ALLOWED_ORIGINS: str = "*"  # Comma-separated list of allowed origins, or "*" for all
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 10  # Requests per minute per IP
    ENABLE_SECURITY_HEADERS: bool = True

    # Logging configuration
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "json"  # json or console

    # API Documentation configuration
    ENABLE_API_DOCS: bool = True  # Enable OpenAPI/Swagger documentation

    # Request size limits (in bytes)
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024  # 10MB default

    # Session cleanup configuration
    SESSION_RETENTION_DAYS: int = 7  # Delete sessions older than 7 days

    # Feature Flags
    FEATURE_WHATSAPP_ENABLED: bool = False  # Enable WhatsApp integration (frozen for future release)
    FEATURE_IMAGE_GENERATION_ENABLED: bool = False  # Enable image generation (frozen for future release)
    FEATURE_TTS_CACHE_ENABLED: bool = True  # Enable TTS response caching
    FEATURE_DATABASE_TYPE: str = "sqlite"  # Database backend: "sqlite" or "postgresql"
    FEATURE_SESSION_AFFINITY_ENABLED: bool = False  # Enable sticky sessions
    FEATURE_READ_REPLICA_ENABLED: bool = False  # Use read replicas for queries
    FEATURE_MULTI_REGION_ENABLED: bool = False  # Enable multi-region routing

    # Database configuration (for PostgreSQL)
    DATABASE_URL: str | None = None  # PostgreSQL connection string
    DATABASE_READ_REPLICA_URL: str | None = None  # Read replica connection string
    DATABASE_POOL_SIZE: int = 10  # Connection pool size
    DATABASE_MAX_OVERFLOW: int = 20  # Max overflow connections
    DATABASE_URL_US: str | None = None  # US region database
    DATABASE_URL_EU: str | None = None  # EU region database
    DATABASE_URL_ASIA: str | None = None  # Asia region database

    # Speech-to-text configuration
    STT_MAX_RETRIES: int = 3  # Maximum retry attempts for STT
    STT_INITIAL_BACKOFF: float = 1.0  # Initial backoff in seconds
    STT_MAX_BACKOFF: float = 10.0  # Maximum backoff in seconds
    STT_TIMEOUT: int = 60  # API timeout in seconds
    STT_MAX_AUDIO_SIZE_MB: int = 25  # Maximum audio file size in MB

    # Text-to-speech configuration
    TTS_CACHE_ENABLED: bool = True  # Enable TTS response caching
    TTS_CACHE_TTL_HOURS: int = 24  # Cache time-to-live in hours
    TTS_VOICE_STABILITY: float = 0.75  # Voice stability (0.0-1.0)
    TTS_VOICE_SIMILARITY: float = 0.5  # Voice similarity boost (0.0-1.0)
    TTS_MAX_TEXT_LENGTH: int = 5000  # Maximum text length for TTS

    # Audio file cleanup configuration
    AUDIO_CLEANUP_MAX_AGE_HOURS: int = 24  # Delete audio files older than this

    # Circuit breaker configuration
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5  # Failures before opening circuit
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60  # Seconds before attempting recovery

    # LLM timeout and retry configuration
    LLM_TIMEOUT_SECONDS: float = 30.0  # Timeout for LLM API calls
    LLM_MAX_RETRIES: int = 3  # Maximum retry attempts for LLM calls
    LLM_TEMPERATURE_DEFAULT: float = 0.7  # Default temperature for LLM responses
    LLM_TEMPERATURE_ROUTER: float = 0.3  # Temperature for routing decisions
    LLM_TEMPERATURE_MEMORY: float = 0.1  # Temperature for memory extraction
    LLM_TEMPERATURE_IMAGE_SCENARIO: float = 0.4  # Temperature for image scenario generation
    LLM_TEMPERATURE_IMAGE_PROMPT: float = 0.25  # Temperature for image prompt generation

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

    # Image-to-text configuration
    ITT_TIMEOUT_SECONDS: float = 60.0  # Timeout for image-to-text API calls
    ITT_MAX_RETRIES: int = 3  # Maximum retry attempts for image-to-text

    @field_validator("GROQ_API_KEY", "ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID", "TOGETHER_API_KEY", "QDRANT_URL")
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

    @field_validator("FEATURE_DATABASE_TYPE")
    @classmethod
    def validate_database_type(cls, v: str) -> str:
        """Validate database type is either sqlite or postgresql.

        Args:
            v: Database type value

        Returns:
            Validated database type

        Raises:
            ValueError: If database type is not supported
        """
        if v not in ["sqlite", "postgresql"]:
            raise ValueError("FEATURE_DATABASE_TYPE must be 'sqlite' or 'postgresql'")
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
        "LLM_TEMPERATURE_ROUTER",
        "LLM_TEMPERATURE_MEMORY",
        "LLM_TEMPERATURE_IMAGE_SCENARIO",
        "LLM_TEMPERATURE_IMAGE_PROMPT",
        "TTS_VOICE_STABILITY",
        "TTS_VOICE_SIMILARITY",
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
        "ITT_TIMEOUT_SECONDS",
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
                f"{info.field_name} must be a positive number (got {v}). "
                "Timeout values must be greater than 0 seconds."
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
        # Validate DATABASE_URL when using PostgreSQL
        if self.FEATURE_DATABASE_TYPE == "postgresql" and not self.DATABASE_URL:
            raise ValueError(
                "DATABASE_URL is required when FEATURE_DATABASE_TYPE is 'postgresql'. "
                "Please set DATABASE_URL in your .env file with a valid PostgreSQL connection string. "
                "Example: postgresql://user:password@localhost:5432/dbname"
            )

        # Validate WhatsApp configuration when enabled
        if self.FEATURE_WHATSAPP_ENABLED:
            missing_fields = []
            if not self.WHATSAPP_PHONE_NUMBER_ID:
                missing_fields.append("WHATSAPP_PHONE_NUMBER_ID")
            if not self.WHATSAPP_TOKEN:
                missing_fields.append("WHATSAPP_TOKEN")
            if not self.WHATSAPP_VERIFY_TOKEN:
                missing_fields.append("WHATSAPP_VERIFY_TOKEN")

            if missing_fields:
                raise ValueError(
                    f"WhatsApp integration is enabled but the following required fields are missing: "
                    f"{', '.join(missing_fields)}. "
                    "Please set these values in your .env file or disable WhatsApp by setting "
                    "FEATURE_WHATSAPP_ENABLED=false"
                )

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
            logger.info("✓ Qdrant connectivity validated successfully")
        except Exception as e:
            logger.warning(
                f"⚠ Qdrant connectivity check failed: {e}. "
                f"Memory features may not work correctly. "
                f"Please verify QDRANT_URL ({self.QDRANT_URL}) is accessible and QDRANT_API_KEY is valid."
            )

        # Validate database connectivity (PostgreSQL only)
        if self.FEATURE_DATABASE_TYPE == "postgresql" and self.DATABASE_URL:
            try:
                from sqlalchemy import create_engine, text

                engine = create_engine(self.DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 5})
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info("✓ Database connectivity validated successfully")
            except Exception as e:
                logger.warning(
                    f"⚠ Database connectivity check failed: {e}. "
                    f"Persistence features may not work correctly. "
                    f"Please verify DATABASE_URL is accessible and credentials are valid."
                )
        elif self.FEATURE_DATABASE_TYPE == "sqlite":
            # SQLite doesn't need connectivity validation
            logger.info("✓ Using SQLite database (no connectivity check needed)")
        else:
            logger.info("Database connectivity check skipped")


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
        >>> print(settings.TEXT_MODEL_NAME)
        'llama-3.3-70b-versatile'
    """
    try:
        return Settings()  # type: ignore[call-arg]  # Pydantic BaseSettings loads from environment variables
    except ValidationError as e:
        print("❌ Configuration Error: Missing or invalid environment variables", file=sys.stderr)
        print("\nPlease ensure the following environment variables are set:", file=sys.stderr)
        for error in e.errors():
            field = error["loc"][0]
            msg = error["msg"]
            print(f"  - {field}: {msg}", file=sys.stderr)
        print("\nRefer to .env.example for required variables.", file=sys.stderr)
        sys.exit(1)


# Global settings instance - import this in other modules
settings = load_settings()
