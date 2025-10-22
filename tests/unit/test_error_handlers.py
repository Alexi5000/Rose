"""Unit tests for error handler decorators.

This module tests the refactored error handling decorators to ensure they work
correctly for both sync and async functions, handle different error types properly,
and maintain backward compatibility.
"""

from unittest.mock import patch

import pytest
from fastapi import HTTPException

from ai_companion.core.error_handlers import (
    handle_api_errors,
    handle_memory_errors,
    handle_validation_errors,
    handle_workflow_errors,
)
from ai_companion.core.exceptions import (
    CircuitBreakerError,
    ExternalAPIError,
    MemoryError,
    WorkflowError,
)


class TestHandleApiErrors:
    """Tests for handle_api_errors decorator."""

    @pytest.mark.asyncio
    async def test_async_function_success(self):
        """Test that async function executes successfully without errors."""
        @handle_api_errors("test_service")
        async def async_func():
            return "success"

        result = await async_func()
        assert result == "success"

    def test_sync_function_success(self):
        """Test that sync function executes successfully without errors."""
        @handle_api_errors("test_service")
        def sync_func():
            return "success"

        result = sync_func()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_async_circuit_breaker_error(self):
        """Test async function handling of CircuitBreakerError."""
        @handle_api_errors("test_service", "Service unavailable")
        async def async_func():
            raise CircuitBreakerError("Circuit open")

        with pytest.raises(HTTPException) as exc_info:
            await async_func()

        assert exc_info.value.status_code == 503
        assert exc_info.value.detail == "Service unavailable"

    def test_sync_circuit_breaker_error(self):
        """Test sync function handling of CircuitBreakerError."""
        @handle_api_errors("test_service", "Service unavailable")
        def sync_func():
            raise CircuitBreakerError("Circuit open")

        with pytest.raises(HTTPException) as exc_info:
            sync_func()

        assert exc_info.value.status_code == 503
        assert exc_info.value.detail == "Service unavailable"

    @pytest.mark.asyncio
    async def test_async_external_api_error(self):
        """Test async function handling of ExternalAPIError."""
        @handle_api_errors("test_service")
        async def async_func():
            raise ExternalAPIError("API failed")

        with pytest.raises(HTTPException) as exc_info:
            await async_func()

        assert exc_info.value.status_code == 503
        assert exc_info.value.detail == "External service error occurred"

    def test_sync_external_api_error(self):
        """Test sync function handling of ExternalAPIError."""
        @handle_api_errors("test_service")
        def sync_func():
            raise ExternalAPIError("API failed")

        with pytest.raises(HTTPException) as exc_info:
            sync_func()

        assert exc_info.value.status_code == 503
        assert exc_info.value.detail == "External service error occurred"

    @pytest.mark.asyncio
    async def test_async_unexpected_error(self):
        """Test async function handling of unexpected errors."""
        @handle_api_errors("test_service")
        async def async_func():
            raise RuntimeError("Unexpected error")

        with pytest.raises(HTTPException) as exc_info:
            await async_func()

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Internal server error"

    def test_sync_unexpected_error(self):
        """Test sync function handling of unexpected errors."""
        @handle_api_errors("test_service")
        def sync_func():
            raise RuntimeError("Unexpected error")

        with pytest.raises(HTTPException) as exc_info:
            sync_func()

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Internal server error"

    @pytest.mark.asyncio
    @patch("ai_companion.core.error_handlers.logger")
    @patch("ai_companion.core.error_handlers.metrics")
    async def test_async_error_logging_and_metrics(self, mock_metrics, mock_logger):
        """Test that async errors are logged and metrics are recorded."""
        @handle_api_errors("test_service")
        async def async_func():
            raise ExternalAPIError("API failed")

        with pytest.raises(HTTPException):
            await async_func()

        mock_logger.error.assert_called_once()
        mock_metrics.record_error.assert_called_once_with("test_service_api_error")

    @patch("ai_companion.core.error_handlers.logger")
    @patch("ai_companion.core.error_handlers.metrics")
    def test_sync_error_logging_and_metrics(self, mock_metrics, mock_logger):
        """Test that sync errors are logged and metrics are recorded."""
        @handle_api_errors("test_service")
        def sync_func():
            raise ExternalAPIError("API failed")

        with pytest.raises(HTTPException):
            sync_func()

        mock_logger.error.assert_called_once()
        mock_metrics.record_error.assert_called_once_with("test_service_api_error")


class TestHandleWorkflowErrors:
    """Tests for handle_workflow_errors decorator."""

    @pytest.mark.asyncio
    async def test_async_function_success(self):
        """Test that async workflow function executes successfully."""
        @handle_workflow_errors
        async def async_workflow():
            return {"result": "success"}

        result = await async_workflow()
        assert result == {"result": "success"}

    def test_sync_function_success(self):
        """Test that sync workflow function executes successfully."""
        @handle_workflow_errors
        def sync_workflow():
            return {"result": "success"}

        result = sync_workflow()
        assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_async_workflow_error(self):
        """Test async function handling of WorkflowError."""
        @handle_workflow_errors
        async def async_workflow():
            raise WorkflowError("Workflow failed")

        with pytest.raises(HTTPException) as exc_info:
            await async_workflow()

        assert exc_info.value.status_code == 500
        assert "trouble processing your request" in exc_info.value.detail

    def test_sync_workflow_error(self):
        """Test sync function handling of WorkflowError."""
        @handle_workflow_errors
        def sync_workflow():
            raise WorkflowError("Workflow failed")

        with pytest.raises(HTTPException) as exc_info:
            sync_workflow()

        assert exc_info.value.status_code == 500
        assert "trouble processing your request" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_async_unexpected_error(self):
        """Test async function handling of unexpected workflow errors."""
        @handle_workflow_errors
        async def async_workflow():
            raise ValueError("Unexpected error")

        with pytest.raises(HTTPException) as exc_info:
            await async_workflow()

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Internal server error"

    def test_sync_unexpected_error(self):
        """Test sync function handling of unexpected workflow errors."""
        @handle_workflow_errors
        def sync_workflow():
            raise ValueError("Unexpected error")

        with pytest.raises(HTTPException) as exc_info:
            sync_workflow()

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Internal server error"

    @pytest.mark.asyncio
    @patch("ai_companion.core.error_handlers.logger")
    @patch("ai_companion.core.error_handlers.metrics")
    async def test_async_error_logging_and_metrics(self, mock_metrics, mock_logger):
        """Test that async workflow errors are logged and metrics are recorded."""
        @handle_workflow_errors
        async def async_workflow():
            raise WorkflowError("Workflow failed")

        with pytest.raises(HTTPException):
            await async_workflow()

        mock_logger.error.assert_called_once()
        mock_metrics.record_error.assert_called_once_with("workflow_execution_failed")

    @patch("ai_companion.core.error_handlers.logger")
    @patch("ai_companion.core.error_handlers.metrics")
    def test_sync_error_logging_and_metrics(self, mock_metrics, mock_logger):
        """Test that sync workflow errors are logged and metrics are recorded."""
        @handle_workflow_errors
        def sync_workflow():
            raise WorkflowError("Workflow failed")

        with pytest.raises(HTTPException):
            sync_workflow()

        mock_logger.error.assert_called_once()
        mock_metrics.record_error.assert_called_once_with("workflow_execution_failed")


class TestHandleMemoryErrors:
    """Tests for handle_memory_errors decorator."""

    @pytest.mark.asyncio
    async def test_async_function_success(self):
        """Test that async memory function executes successfully."""
        @handle_memory_errors
        async def async_memory_op():
            return "memory_stored"

        result = await async_memory_op()
        assert result == "memory_stored"

    def test_sync_function_success(self):
        """Test that sync memory function executes successfully."""
        @handle_memory_errors
        def sync_memory_op():
            return "memory_stored"

        result = sync_memory_op()
        assert result == "memory_stored"

    @pytest.mark.asyncio
    async def test_async_memory_error_graceful_degradation(self):
        """Test async function gracefully handles MemoryError by returning None."""
        @handle_memory_errors
        async def async_memory_op():
            raise MemoryError("Memory operation failed")

        result = await async_memory_op()
        assert result is None

    def test_sync_memory_error_graceful_degradation(self):
        """Test sync function gracefully handles MemoryError by returning None."""
        @handle_memory_errors
        def sync_memory_op():
            raise MemoryError("Memory operation failed")

        result = sync_memory_op()
        assert result is None

    @pytest.mark.asyncio
    async def test_async_unexpected_error_graceful_degradation(self):
        """Test async function gracefully handles unexpected errors by returning None."""
        @handle_memory_errors
        async def async_memory_op():
            raise RuntimeError("Unexpected error")

        result = await async_memory_op()
        assert result is None

    def test_sync_unexpected_error_graceful_degradation(self):
        """Test sync function gracefully handles unexpected errors by returning None."""
        @handle_memory_errors
        def sync_memory_op():
            raise RuntimeError("Unexpected error")

        result = sync_memory_op()
        assert result is None

    @pytest.mark.asyncio
    @patch("ai_companion.core.error_handlers.logger")
    @patch("ai_companion.core.error_handlers.metrics")
    async def test_async_error_logging_and_metrics(self, mock_metrics, mock_logger):
        """Test that async memory errors are logged and metrics are recorded."""
        @handle_memory_errors
        async def async_memory_op():
            raise MemoryError("Memory operation failed")

        result = await async_memory_op()

        assert result is None
        mock_logger.warning.assert_called_once()
        mock_metrics.record_error.assert_called_once_with("memory_operation_failed")

    @patch("ai_companion.core.error_handlers.logger")
    @patch("ai_companion.core.error_handlers.metrics")
    def test_sync_error_logging_and_metrics(self, mock_metrics, mock_logger):
        """Test that sync memory errors are logged and metrics are recorded."""
        @handle_memory_errors
        def sync_memory_op():
            raise MemoryError("Memory operation failed")

        result = sync_memory_op()

        assert result is None
        mock_logger.warning.assert_called_once()
        mock_metrics.record_error.assert_called_once_with("memory_operation_failed")


class TestHandleValidationErrors:
    """Tests for handle_validation_errors decorator."""

    @pytest.mark.asyncio
    async def test_async_function_success(self):
        """Test that async validation function executes successfully."""
        @handle_validation_errors
        async def async_validate():
            return True

        result = await async_validate()
        assert result is True

    def test_sync_function_success(self):
        """Test that sync validation function executes successfully."""
        @handle_validation_errors
        def sync_validate():
            return True

        result = sync_validate()
        assert result is True

    @pytest.mark.asyncio
    async def test_async_validation_error(self):
        """Test async function handling of ValueError."""
        @handle_validation_errors
        async def async_validate():
            raise ValueError("Invalid input")

        with pytest.raises(HTTPException) as exc_info:
            await async_validate()

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid input"

    def test_sync_validation_error(self):
        """Test sync function handling of ValueError."""
        @handle_validation_errors
        def sync_validate():
            raise ValueError("Invalid input")

        with pytest.raises(HTTPException) as exc_info:
            sync_validate()

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid input"

    @pytest.mark.asyncio
    async def test_async_other_exceptions_propagate(self):
        """Test that async function allows other exceptions to propagate."""
        @handle_validation_errors
        async def async_validate():
            raise RuntimeError("Not a validation error")

        with pytest.raises(RuntimeError) as exc_info:
            await async_validate()

        assert str(exc_info.value) == "Not a validation error"

    def test_sync_other_exceptions_propagate(self):
        """Test that sync function allows other exceptions to propagate."""
        @handle_validation_errors
        def sync_validate():
            raise RuntimeError("Not a validation error")

        with pytest.raises(RuntimeError) as exc_info:
            sync_validate()

        assert str(exc_info.value) == "Not a validation error"

    @pytest.mark.asyncio
    @patch("ai_companion.core.error_handlers.logger")
    @patch("ai_companion.core.error_handlers.metrics")
    async def test_async_error_logging_and_metrics(self, mock_metrics, mock_logger):
        """Test that async validation errors are logged and metrics are recorded."""
        @handle_validation_errors
        async def async_validate():
            raise ValueError("Invalid input")

        with pytest.raises(HTTPException):
            await async_validate()

        mock_logger.warning.assert_called_once()
        mock_metrics.record_error.assert_called_once_with("validation_error")

    @patch("ai_companion.core.error_handlers.logger")
    @patch("ai_companion.core.error_handlers.metrics")
    def test_sync_error_logging_and_metrics(self, mock_metrics, mock_logger):
        """Test that sync validation errors are logged and metrics are recorded."""
        @handle_validation_errors
        def sync_validate():
            raise ValueError("Invalid input")

        with pytest.raises(HTTPException):
            sync_validate()

        mock_logger.warning.assert_called_once()
        mock_metrics.record_error.assert_called_once_with("validation_error")


class TestUserFacingErrorMessages:
    """Tests for user-facing error messages."""

    @pytest.mark.asyncio
    async def test_api_error_default_message(self):
        """Test default user-facing message for API errors."""
        @handle_api_errors("groq")
        async def call_api():
            raise ExternalAPIError("Internal error details")

        with pytest.raises(HTTPException) as exc_info:
            await call_api()

        # Should not expose internal error details
        assert "Internal error details" not in exc_info.value.detail
        assert exc_info.value.detail == "External service error occurred"

    @pytest.mark.asyncio
    async def test_api_error_custom_message(self):
        """Test custom user-facing message for API errors."""
        @handle_api_errors("groq", "Speech recognition is temporarily unavailable")
        async def call_api():
            raise CircuitBreakerError("Circuit open")

        with pytest.raises(HTTPException) as exc_info:
            await call_api()

        assert exc_info.value.detail == "Speech recognition is temporarily unavailable"

    @pytest.mark.asyncio
    async def test_workflow_error_user_friendly_message(self):
        """Test user-friendly message for workflow errors."""
        @handle_workflow_errors
        async def execute_workflow():
            raise WorkflowError("Internal workflow state error")

        with pytest.raises(HTTPException) as exc_info:
            await execute_workflow()

        # Should provide user-friendly message
        assert "trouble processing your request" in exc_info.value.detail
        assert "Internal workflow state error" not in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_validation_error_clear_message(self):
        """Test clear, actionable message for validation errors."""
        @handle_validation_errors
        async def validate_input():
            raise ValueError("Audio file must be less than 10MB")

        with pytest.raises(HTTPException) as exc_info:
            await validate_input()

        # Should provide clear, actionable message
        assert exc_info.value.detail == "Audio file must be less than 10MB"
        assert exc_info.value.status_code == 400
