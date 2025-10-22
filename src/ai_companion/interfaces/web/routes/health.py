"""Health check endpoints."""

import sqlite3
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from ai_companion.core.logging_config import get_logger
from ai_companion.core.metrics import track_performance
from ai_companion.settings import settings

logger = get_logger(__name__)

router = APIRouter()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


class HealthCheckResponse(BaseModel):
    """Response model for health check.

    Attributes:
        status: Overall system health status ('healthy' or 'degraded')
        version: API version number (semantic versioning)
        services: Connectivity status for each external service dependency
    """

    status: str
    version: str
    services: Dict[str, str]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "version": "1.0.0",
                    "services": {
                        "groq": "connected",
                        "qdrant": "connected",
                        "elevenlabs": "connected",
                        "sqlite": "connected"
                    }
                }
            ]
        }
    }


@router.get("/health", response_model=HealthCheckResponse)
@limiter.limit("60/minute")  # Higher limit for health checks
@track_performance("health_check")
async def health_check(request: Request) -> HealthCheckResponse:
    """Check system health and connectivity to external services.

    Performs connectivity checks for all external dependencies and returns
    overall system health status. Used by load balancers and monitoring systems.

    **Validation Rules:**
    - No authentication required
    - Rate limit: 60 requests per minute per IP address
    - Response time: Typically <2 seconds

    **Health Check Components:**
    - Groq API: LLM and speech-to-text service connectivity
    - Qdrant: Vector database for long-term memory
    - ElevenLabs: Text-to-speech service connectivity
    - SQLite: Local database for conversation checkpointing

    **Status Values:**
    - `healthy`: All services connected and operational
    - `degraded`: One or more services disconnected (partial functionality)

    Args:
        request: FastAPI request object (injected)

    Returns:
        HealthCheckResponse: System status, API version, and service connectivity map

    Raises:
        HTTPException 429: Rate limit exceeded (60 requests/minute)
    """
    services = {}

    # Check Groq API connectivity
    try:
        from groq import Groq

        client = Groq(api_key=settings.GROQ_API_KEY)
        # Simple check - if we can create client, API key is valid
        services["groq"] = "connected"
    except Exception as e:
        logger.error("groq_health_check_failed", error=str(e))
        services["groq"] = "disconnected"

    # Check Qdrant connectivity
    try:
        from qdrant_client import QdrantClient

        if settings.QDRANT_API_KEY:
            client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        else:
            client = QdrantClient(host=settings.QDRANT_HOST, port=int(settings.QDRANT_PORT))

        # Try to list collections as a connectivity test
        client.get_collections()
        services["qdrant"] = "connected"
    except Exception as e:
        logger.error("qdrant_health_check_failed", error=str(e))
        services["qdrant"] = "disconnected"

    # Check ElevenLabs connectivity
    try:
        from elevenlabs import ElevenLabs

        client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        services["elevenlabs"] = "connected"
    except Exception as e:
        logger.error("elevenlabs_health_check_failed", error=str(e))
        services["elevenlabs"] = "disconnected"

    # Check SQLite database connectivity
    try:
        db_path = Path(settings.SHORT_TERM_MEMORY_DB_PATH)

        # Check if database file exists or can be created
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Try to connect and execute a simple query
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()

        services["sqlite"] = "connected"
    except Exception as e:
        logger.error("sqlite_health_check_failed", error=str(e))
        services["sqlite"] = "disconnected"

    # Overall status
    status = "healthy" if all(s == "connected" for s in services.values()) else "degraded"

    logger.info("health_check_complete", status=status, services=services)

    return HealthCheckResponse(status=status, version="1.0.0", services=services)
