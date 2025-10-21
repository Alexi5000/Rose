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

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, ValidationError
import sys


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

    @field_validator("GROQ_API_KEY", "ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID", "TOGETHER_API_KEY", "QDRANT_URL")
    @classmethod
    def validate_required_fields(cls, v: str, info) -> str:
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
        return Settings()
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
