"""Standardized error handling decorators for AI Companion application.

This module provides decorators for consistent error handling across the application,
including API error handling, workflow error handling, and general exception handling.

Module Dependencies:
- ai_companion.core.exceptions: Custom exception types (CircuitBreakerError, ExternalAPIError, etc.)
- ai_companion.core.metrics: Metrics recording for error tracking
- fastapi: HTTPException for API error responses
- Standard library: functools, inspect, logging, typing

Dependents (modules that import this):
- Interface modules (web routes, chainlit, whatsapp) for API error handling
- Graph nodes for workflow error handling
- Module implementations for validation error handling

Architecture:
This module is part of the core layer and provides cross-cutting error handling
functionality. It uses function introspection to provide unified decorators that
work with both sync and async functions, eliminating code duplication.

For detailed architecture documentation, see:
- docs/ARCHITECTURE.md: Error Handling Patterns section
- .kiro/specs/technical-debt-management/design.md: Unified Error Handling section

Example:
    >>> @handle_api_errors("groq", "Speech recognition temporarily unavailable")
    >>> async def call_external_api():
    >>>     # API call logic
    >>>     pass
"""

import functools
import inspect
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


def _handle_api_error_logic(
    func_name: str,
    service_name: str,
    fallback_message: Optional[str],
    exception: Exception,
) -> None:
    """Shared error handling logic for API errors.

    This function contains the common error handling logic used by both
    sync and async wrappers in handle_api_errors decorator.

    Args:
        func_name: Name of the function where error occurred
        service_name: Name of the external service
        fallback_message: Optional custom error message for users
        exception: The exception that was caught

    Raises:
        HTTPException: With appropriate status code and message
    """
    if isinstance(exception, CircuitBreakerError):
        logger.error(
            f"Circuit breaker open for {service_name}",
            extra={"service": service_name, "error": str(exception)},
        )
        metrics.record_error(f"{service_name}_circuit_breaker_open")
        message = fallback_message or f"{service_name} service is temporarily unavailable"
        raise HTTPException(status_code=503, detail=message) from exception
    elif isinstance(exception, ExternalAPIError):
        logger.error(
            f"API error in {func_name}",
            extra={"service": service_name, "error": str(exception)},
            exc_info=True,
        )
        metrics.record_error(f"{service_name}_api_error")
        message = fallback_message or "External service error occurred"
        raise HTTPException(status_code=503, detail=message) from exception
    else:
        logger.error(
            f"Unexpected error in {func_name}",
            extra={"service": service_name, "error": str(exception)},
            exc_info=True,
        )
        metrics.record_error(f"{service_name}_unexpected_error")
        raise HTTPException(status_code=500, detail="Internal server error") from exception


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
        # Use introspection to determine if function is async
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    _handle_api_error_logic(func.__name__, service_name, fallback_message, e)

            return async_wrapper  # type: ignore
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    _handle_api_error_logic(func.__name__, service_name, fallback_message, e)

            return sync_wrapper  # type: ignore

    return decorator


def _handle_workflow_error_logic(func_name: str, exception: Exception) -> None:
    """Shared error handling logic for workflow errors.

    This function contains the common error handling logic used by both
    sync and async wrappers in handle_workflow_errors decorator.

    Args:
        func_name: Name of the function where error occurred
        exception: The exception that was caught

    Raises:
        HTTPException: With appropriate status code and message
    """
    if isinstance(exception, WorkflowError):
        logger.error(
            f"Workflow error in {func_name}",
            extra={"error": str(exception)},
            exc_info=True,
        )
        metrics.record_error("workflow_execution_failed")
        raise HTTPException(
            status_code=500,
            detail="I'm having trouble processing your request. Please try again.",
        ) from exception
    else:
        logger.error(
            f"Unexpected workflow error in {func_name}",
            extra={"error": str(exception)},
            exc_info=True,
        )
        metrics.record_error("workflow_unexpected_error")
        raise HTTPException(status_code=500, detail="Internal server error") from exception


def handle_workflow_errors(func: F) -> F:
    """Decorator for handling LangGraph workflow errors with graceful fallbacks.

    This decorator catches workflow execution errors and provides user-friendly
    error messages while logging detailed error information for debugging.

    Args:
        func: Function to decorate

    Returns:
        Decorated function with workflow error handling

    Example:
        >>> @handle_workflow_errors
        >>> async def execute_workflow(state: dict) -> dict:
        >>>     # Workflow execution logic
        >>>     pass
    """

    # Use introspection to determine if function is async
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                _handle_workflow_error_logic(func.__name__, e)

        return async_wrapper  # type: ignore
    else:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                _handle_workflow_error_logic(func.__name__, e)

        return sync_wrapper  # type: ignore


def _handle_memory_error_logic(func_name: str, exception: Exception) -> None:
    """Shared error handling logic for memory errors.

    This function contains the common error handling logic used by both
    sync and async wrappers in handle_memory_errors decorator.
    Returns None to allow graceful degradation.

    Args:
        func_name: Name of the function where error occurred
        exception: The exception that was caught

    Returns:
        None to allow graceful degradation
    """
    if isinstance(exception, MemoryError):
        logger.warning(
            f"Memory operation failed in {func_name}, continuing with degraded memory",
            extra={"error": str(exception)},
        )
        metrics.record_error("memory_operation_failed")
    else:
        logger.error(
            f"Unexpected memory error in {func_name}",
            extra={"error": str(exception)},
            exc_info=True,
        )
        metrics.record_error("memory_unexpected_error")


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

    # Use introspection to determine if function is async
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                _handle_memory_error_logic(func.__name__, e)
                # Return None to allow graceful degradation
                return None

        return async_wrapper  # type: ignore
    else:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                _handle_memory_error_logic(func.__name__, e)
                # Return None to allow graceful degradation
                return None

        return sync_wrapper  # type: ignore


def _handle_validation_error_logic(func_name: str, exception: ValueError) -> None:
    """Shared error handling logic for validation errors.

    This function contains the common error handling logic used by both
    sync and async wrappers in handle_validation_errors decorator.

    Args:
        func_name: Name of the function where error occurred
        exception: The ValueError that was caught

    Raises:
        HTTPException: With status code 400 and validation error message
    """
    logger.warning(
        f"Validation error in {func_name}",
        extra={"error": str(exception)},
    )
    metrics.record_error("validation_error")
    raise HTTPException(status_code=400, detail=str(exception)) from exception


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

    # Use introspection to determine if function is async
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except ValueError as e:
                _handle_validation_error_logic(func.__name__, e)
            except Exception:
                # Let other exceptions propagate
                raise

        return async_wrapper  # type: ignore
    else:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                _handle_validation_error_logic(func.__name__, e)
            except Exception:
                # Let other exceptions propagate
                raise

        return sync_wrapper  # type: ignore
