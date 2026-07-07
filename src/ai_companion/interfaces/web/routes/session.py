"""Session management endpoints."""

import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from ai_companion.core.logging_config import get_logger
from ai_companion.core.metrics import metrics, track_performance
from ai_companion.core.privacy_logging import exc_info_for_log, exception_message_for_log, session_id_for_log
from ai_companion.modules.memory.privacy import (
    MemoryMode,
    get_session_memory_preference,
    sanitize_exported_memories,
    set_session_memory_preference,
)
from ai_companion.modules.memory.provider import get_memory_provider
from ai_companion.settings import settings

logger = get_logger(__name__)

router = APIRouter()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


class SessionStartResponse(BaseModel):
    """Response model for session start.

    Attributes:
        session_id: Unique identifier for the support session (UUID v4 format)
        message: Welcome message confirming session initialization
    """

    session_id: str
    message: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "123e4567-e89b-12d3-a456-426614174000",
                    "message": "Session initialized. Rose is ready for emotional support when you are.",
                }
            ]
        }
    }


class SessionMemoryPreferencesRequest(BaseModel):
    """Request model for updating session memory behavior."""

    memory_mode: Literal["enabled", "session_only"]


class SessionMemoryPreferencesResponse(BaseModel):
    """Response model for session memory behavior."""

    session_id: str
    memory_mode: MemoryMode
    long_term_memory_enabled: bool
    message: str


class SessionMemoryExportResponse(BaseModel):
    """Response model for exporting session memories."""

    session_id: str
    memories: list[dict[str, object]]
    message: str


class SessionMemoryForgetResponse(BaseModel):
    """Response model for deleting session memories."""

    session_id: str
    deleted: bool
    message: str


def _validate_session_id(session_id: str) -> str:
    """Validate that a session ID is a UUID string."""

    try:
        uuid.UUID(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="session_id must be a valid UUID") from exc
    return session_id


def _memory_preferences_response(session_id: str, message: str) -> SessionMemoryPreferencesResponse:
    preference = get_session_memory_preference(session_id)
    return SessionMemoryPreferencesResponse(
        session_id=session_id,
        memory_mode=preference.memory_mode,
        long_term_memory_enabled=preference.long_term_memory_enabled,
        message=message,
    )


@router.post("/session/start", response_model=SessionStartResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
@track_performance("session_start")
async def start_session(request: Request) -> SessionStartResponse:
    """Initialize a new emotional-support session with Rose.

    Generates a unique session_id (UUID v4) that will be used to track conversation
    state, memory context, and support preferences across multiple interactions.

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

    # Record session metrics
    metrics.record_session_started(session_id)

    logger.info("session_started", session_log_id=session_id_for_log(session_id))

    return SessionStartResponse(
        session_id=session_id,
        message="Session initialized. Rose is ready for emotional support when you are.",
    )


@router.get("/session/{session_id}/memory-preferences", response_model=SessionMemoryPreferencesResponse)
async def get_memory_preferences(session_id: str) -> SessionMemoryPreferencesResponse:
    """Return the current long-term memory preference for a session."""

    session_id = _validate_session_id(session_id)
    return _memory_preferences_response(session_id, "Session memory preferences loaded.")


@router.post("/session/{session_id}/memory-preferences", response_model=SessionMemoryPreferencesResponse)
async def update_memory_preferences(
    session_id: str,
    request: SessionMemoryPreferencesRequest,
) -> SessionMemoryPreferencesResponse:
    """Update whether a session may use long-term memory."""

    session_id = _validate_session_id(session_id)
    set_session_memory_preference(session_id, request.memory_mode)
    logger.info(
        "session_memory_preferences_updated",
        session_log_id=session_id_for_log(session_id),
        memory_mode=request.memory_mode,
    )
    if request.memory_mode == "session_only":
        message = "Long-term memory is off for this session. Rose will not store or retrieve memories."
    else:
        message = "Long-term memory is on for this session."
    return _memory_preferences_response(session_id, message)


@router.get("/session/{session_id}/memory/export", response_model=SessionMemoryExportResponse)
async def export_session_memories(session_id: str) -> SessionMemoryExportResponse:
    """Export long-term memories for a session without embedding vectors."""

    session_id = _validate_session_id(session_id)
    try:
        memories = sanitize_exported_memories(get_memory_provider().export_memories_for_session(session_id))
    except Exception as exc:
        logger.error(
            "session_memory_export_failed",
            session_log_id=session_id_for_log(session_id),
            error=exception_message_for_log(exc),
            error_type=type(exc).__name__,
            exc_info=exc_info_for_log(),
        )
        raise HTTPException(status_code=503, detail="Could not export session memories right now.") from exc
    return SessionMemoryExportResponse(
        session_id=session_id,
        memories=memories,
        message=f"Exported {len(memories)} session memories.",
    )


@router.post("/session/{session_id}/memory/forget", response_model=SessionMemoryForgetResponse)
async def forget_session_memories(session_id: str) -> SessionMemoryForgetResponse:
    """Delete long-term memories for a session."""

    session_id = _validate_session_id(session_id)
    try:
        deleted = get_memory_provider().delete_memories_for_session(session_id)
    except Exception as exc:
        logger.error(
            "session_memory_forget_failed",
            session_log_id=session_id_for_log(session_id),
            error=exception_message_for_log(exc),
            error_type=type(exc).__name__,
            exc_info=exc_info_for_log(),
        )
        raise HTTPException(status_code=503, detail="Could not delete session memories right now.") from exc
    if deleted:
        logger.info("session_memories_deleted", session_log_id=session_id_for_log(session_id))
        message = "Long-term memories for this session were deleted."
    else:
        message = "Long-term memory deletion could not be confirmed. Please try again."
    return SessionMemoryForgetResponse(session_id=session_id, deleted=deleted, message=message)
