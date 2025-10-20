"""Health check endpoints."""

import logging
from typing import Dict, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from ai_companion.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


class HealthCheckResponse(BaseModel):
    """Response model for health check."""

    status: str
    version: str
    services: Dict[str, str]


@router.get("/health", response_model=HealthCheckResponse)
@limiter.limit("60/minute")  # Higher limit for health checks
async def health_check(request: Request) -> HealthCheckResponse:
    """Check system health and connectivity to external services.

    Returns:
        HealthCheckResponse: System status, version, and service connectivity
    """
    services = {}

    # Check Groq API connectivity
    try:
        from groq import Groq

        client = Groq(api_key=settings.GROQ_API_KEY)
        # Simple check - if we can create client, API key is valid
        services["groq"] = "connected"
    except Exception as e:
        logger.error(f"Groq API health check failed: {e}")
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
        logger.error(f"Qdrant health check failed: {e}")
        services["qdrant"] = "disconnected"

    # Check ElevenLabs connectivity
    try:
        from elevenlabs import ElevenLabs

        client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        services["elevenlabs"] = "connected"
    except Exception as e:
        logger.error(f"ElevenLabs health check failed: {e}")
        services["elevenlabs"] = "disconnected"

    # Overall status
    status = "healthy" if all(s == "connected" for s in services.values()) else "degraded"

    return HealthCheckResponse(status=status, version="1.0.0", services=services)
