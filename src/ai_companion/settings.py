from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, ValidationError
import sys


class Settings(BaseSettings):
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

    @field_validator("GROQ_API_KEY", "ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID", "TOGETHER_API_KEY", "QDRANT_URL")
    @classmethod
    def validate_required_fields(cls, v: str, info) -> str:
        """Validate that required fields are not empty."""
        if not v or v.strip() == "":
            raise ValueError(f"{info.field_name} is required and cannot be empty")
        return v
    
    def get_allowed_origins(self) -> list[str]:
        """Parse ALLOWED_ORIGINS into a list."""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


def load_settings() -> Settings:
    """Load and validate settings, providing helpful error messages."""
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


settings = load_settings()
