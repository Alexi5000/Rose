"""Standardized error response models and handlers.

This module provides consistent error response formats across all API endpoints,
ensuring clients receive predictable error structures with proper context.
"""

from typing import Any, Dict, Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ai_companion.core.exceptions import (
    AICompanionError,
    ExternalAPIError,
    MemoryError,
    SpeechToTextError,
    TextToSpeechError,
    WorkflowError,
)
from ai_companion.core.logging_config import get_logger

logger = get_logger(__name__)


class ErrorResponse(BaseModel):
    """Standardized error response model.

    Attributes:
        error: Machine-readable error code (snake_case)
        message: Human-readable error message (sanitized for user display)
        request_id: Unique request identifier for tracing
        details: Optional additional context (only in development mode)
    """

    error: str
    message: str
    request_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error": "external_service_unavailable",
                    "message": "I'm having trouble connecting to my services right now. Please try again in a moment.",
                    "request_id": "550e8400-e29b-41d4-a716-446655440000",
                    "details": None,
                }
            ]
        }
    }


def sanitize_error_message(error: Exception, user_friendly: str) -> str:
    """Sanitize error messages to prevent information leakage.

    Args:
        error: Original exception
        user_friendly: User-friendly fallback message

    Returns:
        Sanitized error message safe for user display
    """
    # Never expose internal error details in production
    # Only return user-friendly messages
    return user_friendly


def get_request_id(request: Request) -> Optional[str]:
    """Extract request ID from request state.

    Args:
        request: FastAPI request object

    Returns:
        Request ID if available, None otherwise
    """
    return getattr(request.state, "request_id", None)


async def ai_companion_error_handler(request: Request, exc: AICompanionError) -> JSONResponse:
    """Handle AICompanionError and its subclasses.

    Args:
        request: FastAPI request object
        exc: AICompanionError exception

    Returns:
        JSONResponse with standardized error format
    """
    request_id = get_request_id(request)

    # Log error with context
    logger.error(
        "ai_companion_error",
        error_type=type(exc).__name__,
        error_message=str(exc),
        request_id=request_id,
        exc_info=True,
    )

    # Map exception types to user-friendly messages
    if isinstance(exc, SpeechToTextError):
        error_code = "speech_to_text_failed"
        message = "I couldn't hear that clearly. Could you try again?"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif isinstance(exc, TextToSpeechError):
        error_code = "text_to_speech_failed"
        message = "I'm having trouble with my voice right now, but I'm here."
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif isinstance(exc, MemoryError):
        error_code = "memory_operation_failed"
        message = "I'm having trouble accessing my memories. Let's continue our conversation."
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif isinstance(exc, WorkflowError):
        error_code = "workflow_execution_failed"
        message = "I'm having trouble processing that right now. Could you try rephrasing?"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif isinstance(exc, ExternalAPIError):
        error_code = "external_service_unavailable"
        message = "I'm having trouble connecting to my services right now. Please try again in a moment."
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        error_code = "internal_error"
        message = "Something unexpected happened. Please try again."
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(error=error_code, message=message, request_id=request_id).model_dump(),
    )


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle validation errors with standardized format.

    Args:
        request: FastAPI request object
        exc: Validation exception

    Returns:
        JSONResponse with standardized error format
    """
    request_id = get_request_id(request)

    logger.warning("validation_error", error_message=str(exc), request_id=request_id)

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error="validation_failed",
            message="Invalid request data. Please check your input and try again.",
            request_id=request_id,
        ).model_dump(),
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions with standardized format.

    Args:
        request: FastAPI request object
        exc: Unhandled exception

    Returns:
        JSONResponse with standardized error format
    """
    request_id = get_request_id(request)

    # Log unexpected errors with full context
    logger.error(
        "unhandled_exception",
        error_type=type(exc).__name__,
        error_message=str(exc),
        request_id=request_id,
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="internal_server_error",
            message="An unexpected error occurred. Please try again.",
            request_id=request_id,
        ).model_dump(),
    )
