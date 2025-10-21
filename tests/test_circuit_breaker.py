"""Tests for circuit breaker resilience patterns."""

import asyncio
import time

import pytest

from ai_companion.core.resilience import CircuitBreaker, CircuitBreakerError


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def test_circuit_breaker_closed_state(self):
        """Test that circuit breaker allows calls in CLOSED state."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1, name="TestBreaker")

        def successful_call():
            return "success"

        result = breaker.call(successful_call)
        assert result == "success"
        assert breaker.state == "CLOSED"

    def test_circuit_breaker_opens_after_failures(self):
        """Test that circuit breaker opens after threshold failures."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1, name="TestBreaker")

        def failing_call():
            raise Exception("Service unavailable")

        # First 3 failures should raise the original exception
        for i in range(3):
            with pytest.raises(Exception, match="Service unavailable"):
                breaker.call(failing_call)

        # Circuit should now be OPEN
        assert breaker.state == "OPEN"

        # Next call should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError, match="Circuit breaker is open"):
            breaker.call(failing_call)

    def test_circuit_breaker_half_open_recovery(self):
        """Test that circuit breaker attempts recovery after timeout."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1, name="TestBreaker")

        call_count = [0]

        def flaky_call():
            call_count[0] += 1
            if call_count[0] <= 2:
                raise Exception("Service unavailable")
            return "success"

        # Trigger failures to open circuit
        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(flaky_call)

        assert breaker.state == "OPEN"

        # Wait for recovery timeout
        time.sleep(1.1)

        # Next call should attempt recovery (HALF_OPEN)
        result = breaker.call(flaky_call)
        assert result == "success"
        assert breaker.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_async_circuit_breaker(self):
        """Test circuit breaker with async functions."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1, name="AsyncTestBreaker")

        async def async_failing_call():
            raise Exception("Async service unavailable")

        # Trigger failures
        for _ in range(2):
            with pytest.raises(Exception, match="Async service unavailable"):
                await breaker.call_async(async_failing_call)

        assert breaker.state == "OPEN"

        # Should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            await breaker.call_async(async_failing_call)

    @pytest.mark.asyncio
    async def test_async_circuit_breaker_success(self):
        """Test circuit breaker allows successful async calls."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1, name="AsyncSuccessBreaker")

        async def async_successful_call():
            await asyncio.sleep(0.1)
            return "async success"

        result = await breaker.call_async(async_successful_call)
        assert result == "async success"
        assert breaker.state == "CLOSED"

    def test_circuit_breaker_reset(self):
        """Test manual circuit breaker reset."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=10, name="ResetTestBreaker")

        def failing_call():
            raise Exception("Service unavailable")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(failing_call)

        assert breaker.state == "OPEN"

        # Manually reset
        breaker.reset()
        assert breaker.state == "CLOSED"

        # Should allow calls again
        with pytest.raises(Exception, match="Service unavailable"):
            breaker.call(failing_call)

    def test_circuit_breaker_specific_exception(self):
        """Test circuit breaker only catches expected exceptions."""
        breaker = CircuitBreaker(
            failure_threshold=2, recovery_timeout=1, expected_exception=ValueError, name="SpecificExceptionBreaker"
        )

        def value_error_call():
            raise ValueError("Invalid value")

        def runtime_error_call():
            raise RuntimeError("Runtime error")

        # ValueError should be caught and counted
        with pytest.raises(ValueError):
            breaker.call(value_error_call)

        # RuntimeError should not be caught by circuit breaker
        with pytest.raises(RuntimeError):
            breaker.call(runtime_error_call)

        # Circuit should still be CLOSED (RuntimeError not counted)
        assert breaker.state == "CLOSED"
