"""Session management endpoints."""

import logging
import uuid
from typing import Dict

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class SessionStartResponse(BaseModel):
    """Response model for session start."""

    session_id: str
    message: str


@router.post("/session/start", response_model=SessionStartResponse)
async def start_session() -> SessionStartResponse:
    """Initialize a new healing session.

    Generates a unique session_id that will be used to track conversation
    state across multiple interactions with Rose.

    Returns:
        SessionStartResponse: Contains the session_id and welcome message
    """
    session_id = str(uuid.uuid4())
    logger.info(f"Started new session: {session_id}")

    return SessionStartResponse(
        session_id=session_id,
        message="Session initialized. Ready to begin your healing journey with Rose.",
    )
