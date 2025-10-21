"""Error handling decorators for standardized error management.

This module provides decorators for consistent error handling across
the application, including logging, error transformation, and graceful fallbacks.
"""

import functools
import logging
from typing import Any, Callable, Optional, TypeVar

from fastapi import HTTPException

from ai_companion.core.exceptions import (
    ExternalAPIError,
)
from ai_companion.core.resilience import CircuitBreakerError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def handle_api_errors(
    fallback_status: int = 503,
    fallback_message: str = "Service temporarily unavailable",
) -> Callable:
    """Decorator to handle API errors and convert them to HTTP exceptions.

    This decorator catches external API errors and circuit breaker errors,
    logs them appropriately, and converts them to user-friendly HTTP exceptions.

    Args:
        fallback_status: HTTP status code for fallback response (default: 503)
        fallback_message: User-friendly error message for fallback

    Returns:
        Decorated function that handles API errors gracefully

    Example:
        @handle_api_errors(fallback_status=503, fallback_message="Speech service unavailable")
        async def process_audio(audio_data: bytes) -> str:
            return await stt.transcribe(audio_data)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await func(*args, **kwargs)
            except CircuitBreakerError as e:
                logger.error(
                    f"Circuit breaker open in {func.__name__}: {str(e)}",
                    extra={"function": func.__name__, "error_type": "circuit_breaker"},
                )
                raise HTTPException(
                    status_code=fallback_status,
                    detail=f"{fallback_message} - please try again in a moment",
                )
            except ExternalAPIError as e:
                logger.error(
                    f"External API error in {func.__name__}: {str(e)}",
                    extra={"function": func.__name__, "error_type": type(e).__name__},
                )
                raise HTTPException(status_code=fallback_status, detail=fallback_message)
            except ValueError as e:
                # Validation errors should be returned as 400 Bad Request
                logger.warning(
                    f"Validation error in {func.__name__}: {str(e)}",
                    extra={"function": func.__name__, "error_type": "validation"},
                )
                raise HTTPException(status_code=400, detail=str(e))
            except HTTPException:
                # Re-raise HTTP exceptions as-is
                raise
            except Exception as e:
                logger.error(
                    f"Unexpected error in {func.__name__}: {type(e).__name__}: {str(e)}",
                    exc_info=True,
                    extra={"function": func.__name__, "error_type": "unexpected"},
                )
                raise HTTPException(status_code=500, detail="Internal server error")

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except CircuitBreakerError as e:
                logger.error(
                    f"Circuit breaker open in {func.__name__}: {str(e)}",
                    extra={"function": func.__name__, "error_type": "circuit_breaker"},
                )
                raise HTTPException(
                    status_code=fallback_status,
                    detail=f"{fallback_message} - please try again in a moment",
                )
            except ExternalAPIError as e:
                logger.error(
                    f"External API error in {func.__name__}: {str(e)}",
                    extra={"function": func.__name__, "error_type": type(e).__name__},
                )
                raise HTTPException(status_code=fallback_status, detail=fallback_message)
            except ValueError as e:
                logger.warning(
                    f"Validation error in {func.__name__}: {str(e)}",
                    extra={"function": func.__name__, "error_type": "validation"},
                )
                raise HTTPException(status_code=400, detail=str(e))
            except HTTPException:
                raise
            except Exception as e:
                logger.error(
                    f"Unexpected error in {func.__name__}: {type(e).__name__}: {str(e)}",
                    exc_info=True,
                    extra={"function": func.__name__, "error_type": "unexpected"},
                )
                raise HTTPException(status_code=500, detail="Internal server error")

        # Return appropriate wrapper based on whether function is async
        if functools.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def log_errors(logger_instance: Optional[logging.Logger] = None) -> Callable:
    """Decorator to log errors with context before re-raising.

    This decorator logs errors with full context and traceback,
    then re-raises the original exception for upstream handling.

    Args:
        logger_instance: Optional logger instance to use (defaults to module logger)

    Returns:
        Decorated function that logs errors before re-raising

    Example:
        @log_errors(logger)
        async def process_memory(text: str) -> None:
            await memory_manager.store(text)
    """
    log = logger_instance or logger

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                log.error(
                    f"Error in {func.__name__}: {type(e).__name__}: {str(e)}",
                    exc_info=True,
                    extra={
                        "function": func.__name__,
                        "error_type": type(e).__name__,
                        "args": str(args)[:100],
                        "kwargs": str(kwargs)[:100],
                    },
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log.error(
                    f"Error in {func.__name__}: {type(e).__name__}: {str(e)}",
                    exc_info=True,
                    extra={
                        "function": func.__name__,
                        "error_type": type(e).__name__,
                        "args": str(args)[:100],
                        "kwargs": str(kwargs)[:100],
                    },
                )
                raise

        if functools.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def with_fallback(fallback_value: Any = None, log_level: int = logging.WARNING) -> Callable:
    """Decorator to provide fallback value on error instead of raising.

    This decorator catches all exceptions, logs them, and returns a fallback value
    instead of propagating the error. Useful for non-critical operations.

    Args:
        fallback_value: Value to return on error (default: None)
        log_level: Logging level for error messages (default: WARNING)

    Returns:
        Decorated function that returns fallback value on error

    Example:
        @with_fallback(fallback_value="", log_level=logging.INFO)
        def get_optional_context() -> str:
            return expensive_operation()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.log(
                    log_level,
                    f"Error in {func.__name__}, using fallback: {type(e).__name__}: {str(e)}",
                    extra={"function": func.__name__, "fallback_value": fallback_value},
                )
                return fallback_value

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.log(
                    log_level,
                    f"Error in {func.__name__}, using fallback: {type(e).__name__}: {str(e)}",
                    extra={"function": func.__name__, "fallback_value": fallback_value},
                )
                return fallback_value

        if functools.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
