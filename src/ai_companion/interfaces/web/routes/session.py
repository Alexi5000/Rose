"""Session management endpoints."""

import logging
import uuid
from typing import Dict

from fastapi import APIRouter, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from ai_companion.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


class SessionStartResponse(BaseModel):
    """Response model for session start.
    
    Attributes:
        session_id: Unique identifier for the healing session (UUID v4 format)
        message: Welcome message confirming session initialization
    """

    session_id: str
    message: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "123e4567-e89b-12d3-a456-426614174000",
                    "message": "Session initialized. Ready to begin your healing journey with Rose."
                }
            ]
        }
    }


@router.post("/session/start", response_model=SessionStartResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def start_session(request: Request) -> SessionStartResponse:
    """Initialize a new healing session with Rose.

    Generates a unique session_id (UUID v4) that will be used to track conversation
    state, memory context, and therapeutic progress across multiple interactions.
    
    **Validation Rules:**
    - No request body required
    - Rate limit: 10 requests per minute per IP address
    - Session persistence: Conversations are stored in SQLite with automatic checkpointing
    - Memory: Long-term memories are stored in Qdrant vector database

    **Session Features:**
    - Conversation history tracking
    - Short-term memory (recent messages)
    - Long-term memory (important emotional context)
    - Automatic summarization after 20 messages
    - Session state persists across server restarts

    Args:
        request: FastAPI request object (injected)

    Returns:
        SessionStartResponse: Contains unique session_id (UUID v4) and welcome message

    Raises:
        HTTPException 429: Rate limit exceeded (10 requests/minute)
        HTTPException 500: Internal server error
    """
    session_id = str(uuid.uuid4())
    logger.info(f"Started new session: {session_id}")

    return SessionStartResponse(
        session_id=session_id,
        message="Session initialized. Ready to begin your healing journey with Rose.",
    )
