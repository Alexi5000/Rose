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

    def test_circuit_state_transitions(self):
        """Test complete circuit state transitions: CLOSED → OPEN → HALF_OPEN → CLOSED."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1, name="StateTransitionBreaker")

        call_count = [0]

        def flaky_call():
            call_count[0] += 1
            if call_count[0] <= 2:
                raise Exception("Service unavailable")
            return "success"

        # Initial state: CLOSED
        assert breaker.state == "CLOSED"

        # Trigger failures to transition to OPEN
        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(flaky_call)

        # State should be OPEN
        assert breaker.state == "OPEN"

        # Verify circuit blocks requests while OPEN
        with pytest.raises(CircuitBreakerError):
            breaker.call(flaky_call)

        # Wait for recovery timeout
        time.sleep(1.1)

        # Next call should transition to HALF_OPEN and succeed, then close
        result = breaker.call(flaky_call)
        assert result == "success"
        assert breaker.state == "CLOSED"

    def test_failure_counting_and_threshold(self):
        """Test that failure count increments correctly and respects threshold."""
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=1, name="FailureCountBreaker")

        def failing_call():
            raise Exception("Service error")

        # Fail 4 times - should stay CLOSED
        for i in range(4):
            with pytest.raises(Exception):
                breaker.call(failing_call)
            assert breaker.state == "CLOSED"

        # 5th failure should open circuit
        with pytest.raises(Exception):
            breaker.call(failing_call)
        assert breaker.state == "OPEN"

    def test_recovery_timeout_behavior(self):
        """Test that circuit respects recovery timeout before attempting reset."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=2, name="TimeoutBreaker")

        def failing_call():
            raise Exception("Service unavailable")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(failing_call)

        assert breaker.state == "OPEN"

        # Should block immediately after opening
        with pytest.raises(CircuitBreakerError):
            breaker.call(failing_call)

        # Wait less than recovery timeout
        time.sleep(1)

        # Should still block
        with pytest.raises(CircuitBreakerError):
            breaker.call(failing_call)

        # Wait for full recovery timeout
        time.sleep(1.1)

        # Should now attempt recovery (will fail but transition to HALF_OPEN first)
        with pytest.raises(Exception, match="Service unavailable"):
            breaker.call(failing_call)

    @pytest.mark.asyncio
    async def test_async_circuit_state_transitions(self):
        """Test async circuit state transitions work identically to sync."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1, name="AsyncStateBreaker")

        call_count = [0]

        async def async_flaky_call():
            call_count[0] += 1
            await asyncio.sleep(0.01)
            if call_count[0] <= 2:
                raise Exception("Async service unavailable")
            return "async success"

        # Initial state: CLOSED
        assert breaker.state == "CLOSED"

        # Trigger failures to transition to OPEN
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.call_async(async_flaky_call)

        # State should be OPEN
        assert breaker.state == "OPEN"

        # Wait for recovery timeout
        await asyncio.sleep(1.1)

        # Next call should transition to HALF_OPEN and succeed, then close
        result = await breaker.call_async(async_flaky_call)
        assert result == "async success"
        assert breaker.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_async_failure_counting(self):
        """Test async failure counting matches sync behavior."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1, name="AsyncFailureCountBreaker")

        async def async_failing_call():
            await asyncio.sleep(0.01)
            raise Exception("Async service error")

        # Fail 2 times - should stay CLOSED
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.call_async(async_failing_call)
            assert breaker.state == "CLOSED"

        # 3rd failure should open circuit
        with pytest.raises(Exception):
            await breaker.call_async(async_failing_call)
        assert breaker.state == "OPEN"
