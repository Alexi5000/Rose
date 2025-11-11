"""Server configuration constants for Rose the Healer Shaman.

This module centralizes all magic numbers and configuration values used by the
web interface, eliminating hardcoded values and improving maintainability.

All constants use SCREAMING_SNAKE_CASE naming convention and are organized by
concern with emoji indicators for easy visual scanning.
"""

from pathlib import Path

# 🌐 Network Configuration
# ========================
# Network settings for the web server and development environment

WEB_SERVER_HOST = "0.0.0.0"  # Listen on all interfaces for production
WEB_SERVER_PORT = 8000  # Main web interface port (FastAPI)
DEV_FRONTEND_PORT = 3000  # Vite dev server port for development
DEV_BACKEND_PORT = 8000  # Backend API port for development (same as WEB_SERVER_PORT)
QDRANT_DEFAULT_PORT = 6333  # Default Qdrant vector database port

# 📁 Path Configuration
# =====================
# Filesystem paths for build directories and static assets

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
FRONTEND_SOURCE_DIR = PROJECT_ROOT / "frontend"
FRONTEND_BUILD_DIR = PROJECT_ROOT / "src" / "ai_companion" / "interfaces" / "web" / "static"
AUDIO_TEMP_DIR = PROJECT_ROOT / ".files"  # Temporary audio file storage

# ⏱️ Timeout Configuration
# ========================
# Timeout values for various operations (in seconds)

API_REQUEST_TIMEOUT_SECONDS = 60  # Maximum time for API request processing
WORKFLOW_TIMEOUT_SECONDS = 55  # LangGraph workflow timeout (slightly less than API timeout)
HEALTH_CHECK_TIMEOUT_SECONDS = 5  # Health check endpoint timeout
AUDIO_PROCESSING_TIMEOUT_SECONDS = 30  # Audio transcription and generation timeout

# 📦 File Size Limits
# ===================
# Maximum file sizes for uploads (in bytes and MB)

MAX_AUDIO_FILE_SIZE_MB = 10  # Maximum audio file size in megabytes
MAX_AUDIO_FILE_SIZE_BYTES = MAX_AUDIO_FILE_SIZE_MB * 1024 * 1024  # Converted to bytes
MAX_REQUEST_SIZE_MB = 10  # Maximum HTTP request body size in megabytes
MAX_REQUEST_SIZE_BYTES = MAX_REQUEST_SIZE_MB * 1024 * 1024  # Converted to bytes

# 🔄 Rate Limiting
# ================
# Rate limiting configuration to prevent abuse

RATE_LIMIT_REQUESTS_PER_MINUTE = 10  # Maximum requests per minute per IP address
RATE_LIMIT_ENABLED = True  # Enable/disable rate limiting globally

# 🎨 Asset Configuration
# ======================
# Cache control settings for static assets and API responses

STATIC_ASSET_CACHE_SECONDS = 31536000  # 1 year cache for immutable assets (JS, CSS, images)
HTML_CACHE_SECONDS = 0  # ⚡ No cache for HTML - always get latest (prevents browser cache issues)
API_CACHE_SECONDS = 0  # No cache for API responses (always fresh data)

# 🧹 Cleanup Configuration
# ========================
# Automatic cleanup settings for temporary files and old data

AUDIO_CLEANUP_MAX_AGE_HOURS = 24  # Delete audio files older than 24 hours
AUDIO_CLEANUP_MAX_AGE_SECONDS = AUDIO_CLEANUP_MAX_AGE_HOURS * 3600  # Converted to seconds
AUDIO_CLEANUP_INTERVAL_HOURS = 1  # Run cleanup job every hour
SESSION_CLEANUP_CRON_HOUR = 3  # Run session cleanup at 3 AM daily
SESSION_CLEANUP_CRON_MINUTE = 0  # Minute component of cleanup schedule
DATABASE_BACKUP_CRON_HOUR = 2  # Run database backup at 2 AM daily
DATABASE_BACKUP_CRON_MINUTE = 0  # Minute component of backup schedule
DATABASE_BACKUP_RETENTION_DAYS = 7  # Keep 7 days of database backups

# Time conversion constants
SECONDS_PER_HOUR = 3600  # Number of seconds in one hour

# 🌍 CORS Configuration
# =====================
# Cross-Origin Resource Sharing settings for development and production

DEV_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Vite dev server
    "http://127.0.0.1:3000",  # Alternative localhost
    "http://localhost:8000",  # Backend server (for testing)
    "http://127.0.0.1:8000",  # Alternative localhost
]

PROD_ALLOWED_ORIGINS = ["*"]  # Production: Allow all origins (or configure specific domains)

# 🔌 API Configuration
# ====================
# API endpoint and proxy configuration

API_BASE_PATH = "/api/v1"  # Base path for all API endpoints
API_DOCS_PATH = "/api/v1/docs"  # OpenAPI/Swagger documentation path
API_REDOC_PATH = "/api/v1/redoc"  # ReDoc documentation path
API_OPENAPI_PATH = "/api/v1/openapi.json"  # OpenAPI schema path

# Development proxy configuration for Vite
DEV_API_PROXY_TARGET = f"http://localhost:{DEV_BACKEND_PORT}"  # Backend URL for proxy
DEV_API_PROXY_PATH = "/api"  # Path to proxy to backend

# 📊 Monitoring Configuration
# ===========================
# Logging and monitoring settings

LOG_EMOJI_STARTUP = "🚀"  # Emoji for startup logs
LOG_EMOJI_SUCCESS = "✅"  # Emoji for success logs
LOG_EMOJI_ERROR = "❌"  # Emoji for error logs
LOG_EMOJI_WARNING = "⚠️"  # Emoji for warning logs
LOG_EMOJI_CONNECTION = "🔌"  # Emoji for connection logs
LOG_EMOJI_FRONTEND = "🎨"  # Emoji for frontend-related logs
LOG_EMOJI_VOICE = "🎤"  # Emoji for voice processing logs
LOG_EMOJI_AUDIO = "🔊"  # Emoji for audio playback logs
LOG_EMOJI_METRICS = "📊"  # Emoji for metrics logs
LOG_EMOJI_HEALTH = "🏥"  # Emoji for health check logs
LOG_EMOJI_REQUEST = "📤"  # Emoji for outgoing request logs
LOG_EMOJI_RESPONSE = "📥"  # Emoji for incoming response logs
LOG_EMOJI_CLEANUP = "🧹"  # Emoji for cleanup operation logs
LOG_EMOJI_BACKUP = "💾"  # Emoji for backup operation logs

# 🔒 Security Configuration
# =========================
# Security headers and settings

ENABLE_SECURITY_HEADERS = True  # Enable security headers middleware
ENABLE_REQUEST_ID_TRACKING = True  # Enable request ID middleware for tracing

# 🎯 Application Metadata
# =======================
# Application information for API documentation

APP_TITLE = "Rose the Healer Shaman API"
APP_DESCRIPTION = (
    "Voice-first AI grief counselor and holistic healing companion. "
    "Provides conversational AI interactions with memory persistence, "
    "voice processing, and therapeutic support."
)
APP_VERSION = "1.0.0"

# 🔧 Development Configuration
# ============================
# Settings specific to development mode

DEV_HOT_RELOAD_ENABLED = True  # Enable hot reload for backend in development
DEV_FRONTEND_HOT_RELOAD_ENABLED = True  # Enable hot reload for frontend in development

# 💬 User-Facing Error Messages
# ==============================
# User-friendly error messages with actionable guidance

# Audio validation errors
ERROR_MSG_AUDIO_TOO_LARGE = (
    f"🎤 Your audio file is too large. Please record a shorter message (maximum {MAX_AUDIO_FILE_SIZE_MB}MB)."
)
ERROR_MSG_AUDIO_EMPTY = (
    "🎤 I didn't receive any audio. Please try recording again and ensure your microphone is working."
)
ERROR_MSG_AUDIO_INVALID_FORMAT = (
    "🎤 I couldn't process that audio format. Please use WAV, MP3, WebM, M4A, or OGG format."
)
ERROR_MSG_AUDIO_VALIDATION_FAILED = (
    "🎤 I couldn't understand that audio. Please try recording again in a quieter environment."
)

# Speech-to-text errors
ERROR_MSG_STT_FAILED = (
    "🎤 I'm having trouble hearing you clearly. Could you try speaking again? "
    "Make sure you're in a quiet environment and speaking clearly into your microphone."
)

# Workflow processing errors
ERROR_MSG_WORKFLOW_TIMEOUT = (
    "⏱️ I'm taking longer than usual to respond. This might be due to high demand. Please try again in a moment."
)
ERROR_MSG_WORKFLOW_FAILED = (
    "💭 I'm having trouble processing your message right now. Please try again. "
    "If this continues, try refreshing the page."
)

# Circuit breaker errors
ERROR_MSG_SERVICE_UNAVAILABLE = (
    "🔌 I'm having trouble connecting to my services right now. "
    "Please wait a moment and try again. If this persists, the service may be temporarily down."
)

# Text-to-speech errors
ERROR_MSG_TTS_FAILED = (
    "🔊 I have a response for you, but I'm having trouble generating the audio. "
    "Here's what I wanted to say: {response_text}"
)

# Audio file serving errors
ERROR_MSG_AUDIO_NOT_FOUND = (
    "🔊 That audio file has expired or doesn't exist. Audio responses are available for 24 hours after generation."
)
ERROR_MSG_AUDIO_SAVE_FAILED = "💾 I generated a response but couldn't save the audio file. Please try again."

# Generic errors
ERROR_MSG_INTERNAL_ERROR = (
    "❌ Something unexpected happened on my end. Please try again. If this keeps happening, please contact support."
)
ERROR_MSG_RATE_LIMIT_EXCEEDED = (
    "⏸️ You're sending messages too quickly. Please wait a moment before trying again. "
    f"(Limit: {RATE_LIMIT_REQUESTS_PER_MINUTE} requests per minute)"
)
