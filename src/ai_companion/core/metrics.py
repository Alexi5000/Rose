"""Application metrics collection and tracking.

This module provides metrics collection for monitoring application behavior,
including session counts, error rates, API usage, and performance metrics.
"""

import time
from collections import defaultdict
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional

from ai_companion.core.logging_config import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """Collects and tracks application metrics.

    Metrics are logged as structured events for consumption by monitoring systems.
    """

    def __init__(self):
        """Initialize metrics collector."""
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, list] = defaultdict(list)

    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, Any]] = None) -> None:
        """Increment a counter metric.

        Args:
            name: Metric name
            value: Increment value (default: 1)
            tags: Optional tags for metric dimensions
        """
        self._counters[name] += value
        logger.info(
            "metric_counter",
            metric_name=name,
            value=value,
            total=self._counters[name],
            tags=tags or {}
        )

    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, Any]] = None) -> None:
        """Set a gauge metric.

        Args:
            name: Metric name
            value: Gauge value
            tags: Optional tags for metric dimensions
        """
        self._gauges[name] = value
        logger.info(
            "metric_gauge",
            metric_name=name,
            value=value,
            tags=tags or {}
        )

    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, Any]] = None) -> None:
        """Record a histogram value.

        Args:
            name: Metric name
            value: Value to record
            tags: Optional tags for metric dimensions
        """
        self._histograms[name].append(value)
        logger.info(
            "metric_histogram",
            metric_name=name,
            value=value,
            tags=tags or {}
        )

    def record_session_started(self, session_id: str) -> None:
        """Record a new session start.

        Args:
            session_id: Session identifier
        """
        self.increment_counter("sessions_started")
        logger.info("session_started", session_id=session_id)

    def record_voice_request(self, session_id: str, audio_size_bytes: int) -> None:
        """Record a voice processing request.

        Args:
            session_id: Session identifier
            audio_size_bytes: Size of audio file in bytes
        """
        self.increment_counter("voice_requests_total")
        self.record_histogram("voice_audio_size_bytes", audio_size_bytes)
        logger.info(
            "voice_request",
            session_id=session_id,
            audio_size_bytes=audio_size_bytes
        )

    def record_api_call(self, service: str, success: bool, duration_ms: float) -> None:
        """Record an external API call.

        Args:
            service: Service name (groq, elevenlabs, qdrant)
            success: Whether the call succeeded
            duration_ms: Call duration in milliseconds
        """
        status = "success" if success else "failure"
        self.increment_counter(f"api_calls_{service}_{status}")
        self.record_histogram(f"api_duration_ms_{service}", duration_ms)
        logger.info(
            "api_call",
            service=service,
            success=success,
            duration_ms=duration_ms
        )

    def record_error(self, error_type: str, endpoint: Optional[str] = None) -> None:
        """Record an error occurrence.

        Args:
            error_type: Type of error
            endpoint: Optional endpoint where error occurred
        """
        tags = {"error_type": error_type}
        if endpoint:
            tags["endpoint"] = endpoint

        self.increment_counter("errors_total", tags=tags)
        logger.error(
            "error_recorded",
            error_type=error_type,
            endpoint=endpoint
        )

    def record_workflow_execution(self, session_id: str, duration_ms: float, success: bool) -> None:
        """Record a workflow execution.

        Args:
            session_id: Session identifier
            duration_ms: Execution duration in milliseconds
            success: Whether execution succeeded
        """
        status = "success" if success else "failure"
        self.increment_counter(f"workflow_executions_{status}")
        self.record_histogram("workflow_duration_ms", duration_ms)
        logger.info(
            "workflow_execution",
            session_id=session_id,
            duration_ms=duration_ms,
            success=success
        )

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all collected metrics.

        Returns:
            Dictionary containing all metrics
        """
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                name: {
                    "count": len(values),
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0,
                    "avg": sum(values) / len(values) if values else 0
                }
                for name, values in self._histograms.items()
            },
            "timestamp": datetime.utcnow().isoformat()
        }


# Global metrics collector instance
metrics = MetricsCollector()


def track_performance(metric_name: Optional[str] = None) -> Callable:
    """Decorator to track endpoint performance.

    Args:
        metric_name: Optional custom metric name (defaults to function name)

    Example:
        @track_performance("voice_processing")
        async def process_voice(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        name = metric_name or func.__name__

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            error_type = None

            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error_type = type(e).__name__
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000

                # Record performance metric
                metrics.record_histogram(f"{name}_duration_ms", duration_ms)

                # Record success/failure
                status = "success" if success else "failure"
                metrics.increment_counter(f"{name}_{status}")

                # Log performance
                log_data = {
                    "endpoint": name,
                    "duration_ms": round(duration_ms, 2),
                    "success": success
                }

                if error_type:
                    log_data["error_type"] = error_type

                logger.info("endpoint_performance", **log_data)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            error_type = None

            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error_type = type(e).__name__
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000

                # Record performance metric
                metrics.record_histogram(f"{name}_duration_ms", duration_ms)

                # Record success/failure
                status = "success" if success else "failure"
                metrics.increment_counter(f"{name}_{status}")

                # Log performance
                log_data = {
                    "endpoint": name,
                    "duration_ms": round(duration_ms, 2),
                    "success": success
                }

                if error_type:
                    log_data["error_type"] = error_type

                logger.info("endpoint_performance", **log_data)

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
