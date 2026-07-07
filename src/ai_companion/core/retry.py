"""Retry utilities for API calls with exponential backoff."""

import logging
import time
from functools import wraps
from typing import Any, Callable, TypeVar, cast

from ai_companion.core.privacy_logging import exc_info_for_log, exception_message_for_log

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_backoff: float = 1.0,
    max_backoff: float = 10.0,
    exceptions: tuple = (Exception,),
    skip_exceptions: tuple = (ValueError, TypeError),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to retry a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff time in seconds
        max_backoff: Maximum backoff time in seconds
        exceptions: Tuple of exceptions to catch and retry
        skip_exceptions: Tuple of exceptions to not retry (raise immediately)

    Returns:
        Decorated function with retry logic

    Example:
        @retry_with_exponential_backoff(max_retries=3)
        def call_api():
            return api.request()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)

                except skip_exceptions as e:
                    # Don't retry validation errors
                    logger.debug(
                        "retry_skipped function=%s error_type=%s error=%s",
                        func.__name__,
                        type(e).__name__,
                        exception_message_for_log(e),
                    )
                    raise

                except exceptions as e:
                    last_exception = e
                    logger.warning(
                        "retry_attempt_failed function=%s attempt=%s max_retries=%s error_type=%s error=%s",
                        func.__name__,
                        attempt + 1,
                        max_retries,
                        type(e).__name__,
                        exception_message_for_log(e),
                        exc_info=exc_info_for_log() and attempt == max_retries - 1,
                    )

                    # If not the last attempt, wait with exponential backoff
                    if attempt < max_retries - 1:
                        backoff_time = min(initial_backoff * (2**attempt), max_backoff)
                        logger.info("retry_wait function=%s backoff_seconds=%.1f", func.__name__, backoff_time)
                        time.sleep(backoff_time)

            # All retries exhausted
            if last_exception is None:
                raise RuntimeError(f"{func.__name__} failed after {max_retries} attempts with no exception captured")
            logger.error(
                "retry_exhausted function=%s max_retries=%s error_type=%s error=%s",
                func.__name__,
                max_retries,
                type(last_exception).__name__,
                exception_message_for_log(last_exception),
            )
            raise last_exception

        return cast(Callable[..., T], wrapper)

    return decorator


async def async_retry_with_exponential_backoff(
    func: Callable[..., Any],  # Async callable that returns T when awaited
    max_retries: int = 3,
    initial_backoff: float = 1.0,
    max_backoff: float = 10.0,
    exceptions: tuple = (Exception,),
    skip_exceptions: tuple = (ValueError, TypeError),
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Async function to retry with exponential backoff.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff time in seconds
        max_backoff: Maximum backoff time in seconds
        exceptions: Tuple of exceptions to catch and retry
        skip_exceptions: Tuple of exceptions to not retry (raise immediately)
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func

    Returns:
        Result from the function

    Raises:
        Last exception if all retries fail

    Example:
        result = await async_retry_with_exponential_backoff(
            api_call,
            max_retries=3,
            arg1="value"
        )
    """
    import asyncio

    last_exception = None

    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)

        except skip_exceptions as e:
            # Don't retry validation errors
            logger.debug(
                "retry_skipped function=%s error_type=%s error=%s",
                func.__name__,
                type(e).__name__,
                exception_message_for_log(e),
            )
            raise

        except exceptions as e:
            last_exception = e
            logger.warning(
                "retry_attempt_failed function=%s attempt=%s max_retries=%s error_type=%s error=%s",
                func.__name__,
                attempt + 1,
                max_retries,
                type(e).__name__,
                exception_message_for_log(e),
                exc_info=exc_info_for_log() and attempt == max_retries - 1,
            )

            # If not the last attempt, wait with exponential backoff
            if attempt < max_retries - 1:
                backoff_time = min(initial_backoff * (2**attempt), max_backoff)
                logger.info("retry_wait function=%s backoff_seconds=%.1f", func.__name__, backoff_time)
                await asyncio.sleep(backoff_time)

    # All retries exhausted
    if last_exception is None:
        raise RuntimeError(f"{func.__name__} failed after {max_retries} attempts with no exception captured")
    logger.error(
        "retry_exhausted function=%s max_retries=%s error_type=%s error=%s",
        func.__name__,
        max_retries,
        type(last_exception).__name__,
        exception_message_for_log(last_exception),
    )
    raise last_exception
