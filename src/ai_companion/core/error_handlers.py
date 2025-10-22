"""Standardized error handling decorators for AI Companion application.

This module provides decorators for consistent error handling across the application,
including API error handling, workflow error handling, and general exception handling.

Example:
    >>> @handle_api_errors
    >>> async def call_external_api():
    >>>     # API call logic
    >>>     pass
"""

import functools
import logging
from typing import Any, Callable, Optional, TypeVar

from fastapi import HTTPException

from ai_companion.core.exceptions import (
    CircuitBreakerError,
    ExternalAPIError,
    MemoryError,
    WorkflowError,
)
from ai_companion.core.metrics import metrics

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def handle_api_errors(
    service_name: str,
    fallback_message: Optional[str] = None,
) -> Callable[[F], F]:
    """Decorator for handling external API errors with consistent logging and metrics.

    This decorator catches and handles errors from external services (Groq, ElevenLabs, Qdrant)
    with proper logging, metrics recording, and user-friendly error messages.

    Args:
        service_name: Name of the external service (e.g., "groq", "elevenlabs", "qdrant")
        fallback_message: Optional custom error message for users

    Returns:
        Decorated function with error handling

    Example:
        >>> @handle_api_errors("groq", "Speech recognition is temporarily unavailable")
        >>> async def transcribe_audio(audio_data: bytes) -> str:
        >>>     # Transcription logic
        >>>     pass
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except CircuitBreakerError as e:
                logger.error(
                    f"Circuit breaker open for {service_name}",
                    extra={"service": service_name, "error": str(e)},
                )
                metrics.record_error(f"{service_name}_circuit_breaker_open")
                message = fallback_message or f"{service_name} service is temporarily unavailable"
                raise HTTPException(status_code=503, detail=message) from e
            except ExternalAPIError as e:
                logger.error(
                    f"API error in {func.__name__}",
                    extra={"service": service_name, "error": str(e)},
                    exc_info=True,
                )
                metrics.record_error(f"{service_name}_api_error")
                message = fallback_message or "External service error occurred"
                raise HTTPException(status_code=503, detail=message) from e
            except Exception as e:
                logger.error(
                    f"Unexpected error in {func.__name__}",
                    extra={"service": service_name, "error": str(e)},
                    exc_info=True,
                )
                metrics.record_error(f"{service_name}_unexpected_error")
                raise HTTPException(status_code=500, detail="Internal server error") from e

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except CircuitBreakerError as e:
                logger.error(
                    f"Circuit breaker open for {service_name}",
                    extra={"service": service_name, "error": str(e)},
                )
                metrics.record_error(f"{service_name}_circuit_breaker_open")
                message = fallback_message or f"{service_name} service is temporarily unavailable"
                raise HTTPException(status_code=503, detail=message) from e
            except ExternalAPIError as e:
                logger.error(
                    f"API error in {func.__name__}",
                    extra={"service": service_name, "error": str(e)},
                    exc_info=True,
                )
                metrics.record_error(f"{service_name}_api_error")
                message = fallback_message or "External service error occurred"
                raise HTTPException(status_code=503, detail=message) from e
            except Exception as e:
                logger.error(
                    f"Unexpected error in {func.__name__}",
                    extra={"service": service_name, "error": str(e)},
                    exc_info=True,
                )
                metrics.record_error(f"{service_name}_unexpected_error")
                raise HTTPException(status_code=500, detail="Internal server error") from e

        # Return appropriate wrapper based on function type
        if functools.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


def handle_workflow_errors(func: F) -> F:
    """Decorator for handling LangGraph workflow errors with graceful fallbacks.

    This decorator catches workflow execution errors and provides user-friendly
    error messages while logging detailed error information for debugging.

    Args:
        func: Function to decorate (must be async)

    Returns:
        Decorated function with workflow error handling

    Example:
        >>> @handle_workflow_errors
        >>> async def execute_workflow(state: dict) -> dict:
        >>>     # Workflow execution logic
        >>>     pass
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except WorkflowError as e:
            logger.error(
                f"Workflow error in {func.__name__}",
                extra={"error": str(e)},
                exc_info=True,
            )
            metrics.record_error("workflow_execution_failed")
            raise HTTPException(
                status_code=500,
                detail="I'm having trouble processing your request. Please try again.",
            ) from e
        except Exception as e:
            logger.error(
                f"Unexpected workflow error in {func.__name__}",
                extra={"error": str(e)},
                exc_info=True,
            )
            metrics.record_error("workflow_unexpected_error")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    return wrapper  # type: ignore


def handle_memory_errors(func: F) -> F:
    """Decorator for handling memory operation errors with graceful degradation.

    This decorator catches memory-related errors (Qdrant, SQLite) and allows
    the application to continue functioning with degraded memory capabilities.

    Args:
        func: Function to decorate

    Returns:
        Decorated function with memory error handling

    Example:
        >>> @handle_memory_errors
        >>> async def store_memory(text: str) -> None:
        >>>     # Memory storage logic
        >>>     pass
    """

    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except MemoryError as e:
            logger.warning(
                f"Memory operation failed in {func.__name__}, continuing with degraded memory",
                extra={"error": str(e)},
            )
            metrics.record_error("memory_operation_failed")
            # Return None or empty result to allow graceful degradation
            return None
        except Exception as e:
            logger.error(
                f"Unexpected memory error in {func.__name__}",
                extra={"error": str(e)},
                exc_info=True,
            )
            metrics.record_error("memory_unexpected_error")
            # Return None to allow graceful degradation
            return None

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except MemoryError as e:
            logger.warning(
                f"Memory operation failed in {func.__name__}, continuing with degraded memory",
                extra={"error": str(e)},
            )
            metrics.record_error("memory_operation_failed")
            # Return None or empty result to allow graceful degradation
            return None
        except Exception as e:
            logger.error(
                f"Unexpected memory error in {func.__name__}",
                extra={"error": str(e)},
                exc_info=True,
            )
            metrics.record_error("memory_unexpected_error")
            # Return None to allow graceful degradation
            return None

    # Return appropriate wrapper based on function type
    if functools.iscoroutinefunction(func):
        return async_wrapper  # type: ignore
    else:
        return sync_wrapper  # type: ignore


def handle_validation_errors(func: F) -> F:
    """Decorator for handling validation errors with clear user feedback.

    This decorator catches validation errors (ValueError, Pydantic ValidationError)
    and returns clear, actionable error messages to users.

    Args:
        func: Function to decorate

    Returns:
        Decorated function with validation error handling

    Example:
        >>> @handle_validation_errors
        >>> async def validate_audio(audio_data: bytes) -> bool:
        >>>     # Validation logic
        >>>     pass
    """

    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            logger.warning(
                f"Validation error in {func.__name__}",
                extra={"error": str(e)},
            )
            metrics.record_error("validation_error")
            raise HTTPException(status_code=400, detail=str(e)) from e
        except Exception:
            # Let other exceptions propagate
            raise

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            logger.warning(
                f"Validation error in {func.__name__}",
                extra={"error": str(e)},
            )
            metrics.record_error("validation_error")
            raise HTTPException(status_code=400, detail=str(e)) from e
        except Exception:
            # Let other exceptions propagate
            raise

    # Return appropriate wrapper based on function type
    if functools.iscoroutinefunction(func):
        return async_wrapper  # type: ignore
    else:
        return sync_wrapper  # type: ignore
