"""Resilience patterns including circuit breakers for external service calls."""

import logging
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

# Type variable for generic function signatures
F = TypeVar("F", bound=Callable[..., Any])


class CircuitBreakerError(Exception):
    """Raised when a circuit breaker is open and prevents execution."""

    pass


class CircuitBreaker:
    """Circuit breaker implementation for external service calls.

    The circuit breaker has three states:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests are blocked
    - HALF_OPEN: Testing if service has recovered

    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        expected_exception: Exception type to catch (defaults to Exception)
        name: Name for logging purposes
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type[Exception] = Exception,
        name: str = "CircuitBreaker",
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name

        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    @property
    def state(self) -> str:
        """Get current circuit breaker state."""
        return self._state

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self._last_failure_time is None:
            return False

        import time

        return (time.time() - self._last_failure_time) >= self.recovery_timeout

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func execution

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Original exception if circuit is closed
        """
        # Check if circuit is open
        if self._state == "OPEN":
            if self._should_attempt_reset():
                logger.info(f"{self.name}: Attempting recovery (HALF_OPEN)")
                self._state = "HALF_OPEN"
            else:
                logger.warning(f"{self.name}: Circuit is OPEN, blocking request")
                raise CircuitBreakerError(f"{self.name}: Circuit breaker is open, service unavailable")

        try:
            result = func(*args, **kwargs)

            # Success - reset failure count if in HALF_OPEN state
            if self._state == "HALF_OPEN":
                logger.info(f"{self.name}: Recovery successful, closing circuit")
                self._state = "CLOSED"
                self._failure_count = 0
                self._last_failure_time = None

            return result

        except self.expected_exception as e:
            self._failure_count += 1
            logger.warning(
                f"{self.name}: Failure {self._failure_count}/{self.failure_threshold} - {type(e).__name__}: {str(e)}"
            )

            # Open circuit if threshold reached
            if self._failure_count >= self.failure_threshold:
                import time

                self._state = "OPEN"
                self._last_failure_time = time.time()
                logger.error(
                    f"{self.name}: Circuit breaker OPENED after {self._failure_count} failures. "
                    f"Will retry in {self.recovery_timeout}s"
                )

            # Re-raise the original exception
            raise

    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func execution

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Original exception if circuit is closed
        """
        # Check if circuit is open
        if self._state == "OPEN":
            if self._should_attempt_reset():
                logger.info(f"{self.name}: Attempting recovery (HALF_OPEN)")
                self._state = "HALF_OPEN"
            else:
                logger.warning(f"{self.name}: Circuit is OPEN, blocking request")
                raise CircuitBreakerError(f"{self.name}: Circuit breaker is open, service unavailable")

        try:
            result = await func(*args, **kwargs)

            # Success - reset failure count if in HALF_OPEN state
            if self._state == "HALF_OPEN":
                logger.info(f"{self.name}: Recovery successful, closing circuit")
                self._state = "CLOSED"
                self._failure_count = 0
                self._last_failure_time = None

            return result

        except self.expected_exception as e:
            self._failure_count += 1
            logger.warning(
                f"{self.name}: Failure {self._failure_count}/{self.failure_threshold} - {type(e).__name__}: {str(e)}"
            )

            # Open circuit if threshold reached
            if self._failure_count >= self.failure_threshold:
                import time

                self._state = "OPEN"
                self._last_failure_time = time.time()
                logger.error(
                    f"{self.name}: Circuit breaker OPENED after {self._failure_count} failures. "
                    f"Will retry in {self.recovery_timeout}s"
                )

            # Re-raise the original exception
            raise

    def reset(self) -> None:
        """Manually reset the circuit breaker to CLOSED state."""
        logger.info(f"{self.name}: Manually resetting circuit breaker")
        self._state = "CLOSED"
        self._failure_count = 0
        self._last_failure_time = None


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: type[Exception] = Exception,
    name: Optional[str] = None,
) -> Callable[[F], F]:
    """Decorator to add circuit breaker protection to a function.

    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        expected_exception: Exception type to catch
        name: Name for logging (defaults to function name)

    Returns:
        Decorated function with circuit breaker protection

    Example:
        @circuit_breaker(failure_threshold=3, recovery_timeout=30)
        async def call_external_api():
            # API call logic
            pass
    """
    breaker = CircuitBreaker(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        expected_exception=expected_exception,
        name=name or "CircuitBreaker",
    )

    def decorator(func: F) -> F:
        if hasattr(func, "__self__"):
            # Instance method
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await breaker.call_async(func, *args, **kwargs)

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return breaker.call(func, *args, **kwargs)

        else:
            # Regular function
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await breaker.call_async(func, *args, **kwargs)

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return breaker.call(func, *args, **kwargs)

        # Return appropriate wrapper based on whether function is async
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


# Global circuit breakers for external services
groq_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=Exception,
    name="GroqAPI",
)

elevenlabs_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=Exception,
    name="ElevenLabsAPI",
)

qdrant_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=Exception,
    name="QdrantAPI",
)


def get_groq_circuit_breaker() -> CircuitBreaker:
    """Get the global Groq circuit breaker instance."""
    return groq_circuit_breaker


def get_elevenlabs_circuit_breaker() -> CircuitBreaker:
    """Get the global ElevenLabs circuit breaker instance."""
    return elevenlabs_circuit_breaker


def get_qdrant_circuit_breaker() -> CircuitBreaker:
    """Get the global Qdrant circuit breaker instance."""
    return qdrant_circuit_breaker
