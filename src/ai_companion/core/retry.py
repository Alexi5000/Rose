"""Retry utilities for API calls with exponential backoff."""

import logging
import time
from functools import wraps
from typing import Any, Callable, TypeVar, cast

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
                    logger.debug(f"Skipping retry for {type(e).__name__}: {str(e)}")
                    raise

                except exceptions as e:
                    last_exception = e
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1}/{max_retries} failed: "
                        f"{type(e).__name__}: {str(e)}",
                        exc_info=attempt == max_retries - 1,  # Full traceback on last attempt
                    )

                    # If not the last attempt, wait with exponential backoff
                    if attempt < max_retries - 1:
                        backoff_time = min(initial_backoff * (2**attempt), max_backoff)
                        logger.info(f"Retrying {func.__name__} in {backoff_time:.1f} seconds...")
                        time.sleep(backoff_time)

            # All retries exhausted
            if last_exception is None:
                raise RuntimeError(f"{func.__name__} failed after {max_retries} attempts with no exception captured")
            error_msg = f"{func.__name__} failed after {max_retries} attempts: {str(last_exception)}"
            logger.error(error_msg)
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
            logger.debug(f"Skipping retry for {type(e).__name__}: {str(e)}")
            raise

        except exceptions as e:
            last_exception = e
            logger.warning(
                f"{func.__name__} attempt {attempt + 1}/{max_retries} failed: " f"{type(e).__name__}: {str(e)}",
                exc_info=attempt == max_retries - 1,  # Full traceback on last attempt
            )

            # If not the last attempt, wait with exponential backoff
            if attempt < max_retries - 1:
                backoff_time = min(initial_backoff * (2**attempt), max_backoff)
                logger.info(f"Retrying {func.__name__} in {backoff_time:.1f} seconds...")
                await asyncio.sleep(backoff_time)

    # All retries exhausted
    if last_exception is None:
        raise RuntimeError(f"{func.__name__} failed after {max_retries} attempts with no exception captured")
    error_msg = f"{func.__name__} failed after {max_retries} attempts: {str(last_exception)}"
    logger.error(error_msg)
    raise last_exception
