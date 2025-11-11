"""Monitoring and alerting system for Rose application.

This module provides comprehensive monitoring capabilities including:
- Alert threshold monitoring for errors, response times, and memory
- Integration with external monitoring services (Sentry)
- Metrics aggregation and reporting
- Health status tracking
"""

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ai_companion.core.logging_config import get_logger
from ai_companion.core.metrics import metrics

logger = get_logger(__name__)


@dataclass
class AlertThreshold:
    """Configuration for an alert threshold.

    Attributes:
        name: Alert name
        metric_name: Name of the metric to monitor
        threshold: Threshold value that triggers the alert
        comparison: Comparison operator ('gt', 'lt', 'gte', 'lte', 'eq')
        window_seconds: Time window for evaluation
        enabled: Whether the alert is enabled
    """

    name: str
    metric_name: str
    threshold: float
    comparison: str = "gt"  # gt, lt, gte, lte, eq
    window_seconds: int = 300  # 5 minutes default
    enabled: bool = True


@dataclass
class Alert:
    """Represents a triggered alert.

    Attributes:
        name: Alert name
        message: Alert message
        severity: Alert severity (critical, warning, info)
        metric_value: Current metric value
        threshold: Threshold that was exceeded
        timestamp: When the alert was triggered
    """

    name: str
    message: str
    severity: str
    metric_value: float
    threshold: float
    timestamp: datetime


class MonitoringSystem:
    """Central monitoring and alerting system.

    This class manages alert thresholds, evaluates metrics against thresholds,
    and integrates with external monitoring services.
    """

    def __init__(self):
        """Initialize monitoring system."""
        self._alert_thresholds: List[AlertThreshold] = []
        self._active_alerts: List[Alert] = []
        self._alert_history: List[Alert] = []
        self._last_evaluation = datetime.utcnow()
        self._sentry_enabled = False

        # Initialize Sentry if configured
        self._init_sentry()

        # Set up default alert thresholds
        self._setup_default_thresholds()

    def _init_sentry(self) -> None:
        """Initialize Sentry error tracking if configured."""
        sentry_dsn = os.getenv("SENTRY_DSN")

        if sentry_dsn:
            try:
                import sentry_sdk
                from sentry_sdk.integrations.fastapi import FastApiIntegration
                from sentry_sdk.integrations.logging import LoggingIntegration

                # Configure Sentry
                sentry_sdk.init(
                    dsn=sentry_dsn,
                    environment=os.getenv("ENVIRONMENT", "production"),
                    traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
                    profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
                    integrations=[
                        FastApiIntegration(),
                        LoggingIntegration(
                            level=None,  # Capture all logs
                            event_level=None,  # Send errors as events
                        ),
                    ],
                    # Set release version
                    release=os.getenv("APP_VERSION", "1.0.0"),
                    # Additional configuration
                    attach_stacktrace=True,
                    send_default_pii=False,  # Don't send PII
                )

                self._sentry_enabled = True
                logger.info("sentry_initialized", dsn_configured=True)

            except ImportError:
                logger.warning("sentry_not_available", message="Sentry DSN configured but sentry-sdk not installed")
            except Exception as e:
                logger.error("sentry_init_failed", error=str(e))
        else:
            logger.info("sentry_not_configured", message="SENTRY_DSN not set")

    def _setup_default_thresholds(self) -> None:
        """Set up default alert thresholds."""
        # Error rate threshold: > 5% of requests failing
        self.add_threshold(
            AlertThreshold(
                name="high_error_rate",
                metric_name="error_rate_percent",
                threshold=5.0,
                comparison="gt",
                window_seconds=300,  # 5 minutes
                enabled=os.getenv("ALERT_ERROR_RATE_ENABLED", "true").lower() == "true",
            )
        )

        # Response time threshold: P95 > 2000ms
        self.add_threshold(
            AlertThreshold(
                name="slow_response_time",
                metric_name="response_time_p95_ms",
                threshold=2000.0,
                comparison="gt",
                window_seconds=300,
                enabled=os.getenv("ALERT_RESPONSE_TIME_ENABLED", "true").lower() == "true",
            )
        )

        # Memory usage threshold: > 80% of limit
        self.add_threshold(
            AlertThreshold(
                name="high_memory_usage",
                metric_name="memory_usage_percent",
                threshold=80.0,
                comparison="gt",
                window_seconds=60,  # 1 minute
                enabled=os.getenv("ALERT_MEMORY_ENABLED", "true").lower() == "true",
            )
        )

        # Circuit breaker open threshold
        self.add_threshold(
            AlertThreshold(
                name="circuit_breaker_open",
                metric_name="circuit_breaker_open_count",
                threshold=0.0,
                comparison="gt",
                window_seconds=60,
                enabled=os.getenv("ALERT_CIRCUIT_BREAKER_ENABLED", "true").lower() == "true",
            )
        )

        logger.info("alert_thresholds_configured", count=len(self._alert_thresholds))

    def add_threshold(self, threshold: AlertThreshold) -> None:
        """Add an alert threshold.

        Args:
            threshold: Alert threshold configuration
        """
        self._alert_thresholds.append(threshold)
        logger.info(
            "alert_threshold_added",
            name=threshold.name,
            metric=threshold.metric_name,
            threshold=threshold.threshold,
            enabled=threshold.enabled,
        )

    def evaluate_thresholds(self) -> List[Alert]:
        """Evaluate all alert thresholds against current metrics.

        Returns:
            List of triggered alerts
        """
        triggered_alerts = []
        current_time = datetime.utcnow()

        # Get current metrics
        metrics_summary = metrics.get_metrics_summary()

        # Calculate derived metrics
        derived_metrics = self._calculate_derived_metrics(metrics_summary)

        # Evaluate each threshold
        for threshold in self._alert_thresholds:
            if not threshold.enabled:
                continue

            # Get metric value
            metric_value = derived_metrics.get(threshold.metric_name)

            if metric_value is None:
                continue

            # Check if threshold is exceeded
            if self._check_threshold(metric_value, threshold):
                alert = Alert(
                    name=threshold.name,
                    message=self._format_alert_message(threshold, metric_value),
                    severity=self._get_alert_severity(threshold.name),
                    metric_value=metric_value,
                    threshold=threshold.threshold,
                    timestamp=current_time,
                )

                triggered_alerts.append(alert)
                self._handle_alert(alert)

        self._last_evaluation = current_time
        return triggered_alerts

    def _calculate_derived_metrics(self, metrics_summary: Dict[str, Any]) -> Dict[str, float]:
        """Calculate derived metrics from raw metrics.

        Args:
            metrics_summary: Raw metrics summary

        Returns:
            Dictionary of derived metrics
        """
        derived = {}
        counters = metrics_summary.get("counters", {})
        histograms = metrics_summary.get("histograms", {})

        # Calculate error rate percentage
        total_requests = sum(v for k, v in counters.items() if k.endswith("_success") or k.endswith("_failure"))
        total_errors = sum(v for k, v in counters.items() if k.endswith("_failure") or k == "errors_total")

        if total_requests > 0:
            derived["error_rate_percent"] = (total_errors / total_requests) * 100
        else:
            derived["error_rate_percent"] = 0.0

        # Calculate P95 response time
        response_times = []
        for name, hist_data in histograms.items():
            if "duration_ms" in name:
                # Use max as approximation for P95 (simplified)
                response_times.append(hist_data.get("max", 0))

        if response_times:
            derived["response_time_p95_ms"] = max(response_times)
        else:
            derived["response_time_p95_ms"] = 0.0

        # Get memory usage (if available from system metrics)
        try:
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()

            derived["memory_usage_bytes"] = memory_info.rss
            derived["memory_usage_percent"] = memory_percent
        except ImportError:
            derived["memory_usage_percent"] = 0.0

        # Count open circuit breakers
        circuit_breaker_open = sum(1 for k, v in counters.items() if "circuit_breaker" in k and "open" in k and v > 0)
        derived["circuit_breaker_open_count"] = circuit_breaker_open

        return derived

    def _check_threshold(self, value: float, threshold: AlertThreshold) -> bool:
        """Check if a value exceeds a threshold.

        Args:
            value: Current metric value
            threshold: Threshold configuration

        Returns:
            True if threshold is exceeded
        """
        if threshold.comparison == "gt":
            return value > threshold.threshold
        elif threshold.comparison == "gte":
            return value >= threshold.threshold
        elif threshold.comparison == "lt":
            return value < threshold.threshold
        elif threshold.comparison == "lte":
            return value <= threshold.threshold
        elif threshold.comparison == "eq":
            return value == threshold.threshold
        return False

    def _format_alert_message(self, threshold: AlertThreshold, value: float) -> str:
        """Format an alert message.

        Args:
            threshold: Alert threshold
            value: Current metric value

        Returns:
            Formatted alert message
        """
        return (
            f"Alert: {threshold.name} - {threshold.metric_name} is {value:.2f} (threshold: {threshold.threshold:.2f})"
        )

    def _get_alert_severity(self, alert_name: str) -> str:
        """Get alert severity based on alert name.

        Args:
            alert_name: Name of the alert

        Returns:
            Severity level (critical, warning, info)
        """
        critical_alerts = ["high_error_rate", "high_memory_usage", "circuit_breaker_open"]

        if alert_name in critical_alerts:
            return "critical"
        return "warning"

    def _handle_alert(self, alert: Alert) -> None:
        """Handle a triggered alert.

        Args:
            alert: Triggered alert
        """
        # Log the alert
        logger.warning(
            "alert_triggered",
            alert_name=alert.name,
            severity=alert.severity,
            metric_value=alert.metric_value,
            threshold=alert.threshold,
            message=alert.message,
        )

        # Send to Sentry if enabled and critical
        if self._sentry_enabled and alert.severity == "critical":
            try:
                import sentry_sdk

                sentry_sdk.capture_message(
                    alert.message,
                    level="error",
                    extras={
                        "alert_name": alert.name,
                        "metric_value": alert.metric_value,
                        "threshold": alert.threshold,
                        "severity": alert.severity,
                    },
                )
            except Exception as e:
                logger.error("sentry_alert_failed", error=str(e))

        # Add to active alerts
        self._active_alerts.append(alert)
        self._alert_history.append(alert)

        # Keep only recent alerts in active list (last hour)
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        self._active_alerts = [a for a in self._active_alerts if a.timestamp > cutoff_time]

    def get_active_alerts(self) -> List[Alert]:
        """Get currently active alerts.

        Returns:
            List of active alerts
        """
        return self._active_alerts

    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for the specified time period.

        Args:
            hours: Number of hours of history to retrieve

        Returns:
            List of historical alerts
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [alert for alert in self._alert_history if alert.timestamp > cutoff_time]

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get overall monitoring system status.

        Returns:
            Dictionary with monitoring status information
        """
        return {
            "sentry_enabled": self._sentry_enabled,
            "alert_thresholds_count": len(self._alert_thresholds),
            "active_alerts_count": len(self._active_alerts),
            "last_evaluation": self._last_evaluation.isoformat(),
            "active_alerts": [
                {
                    "name": alert.name,
                    "severity": alert.severity,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                }
                for alert in self._active_alerts
            ],
        }

    def capture_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Capture an exception for error tracking.

        Args:
            exception: Exception to capture
            context: Optional context information
        """
        if self._sentry_enabled:
            try:
                import sentry_sdk

                with sentry_sdk.push_scope() as scope:
                    if context:
                        for key, value in context.items():
                            scope.set_extra(key, value)
                    sentry_sdk.capture_exception(exception)
            except Exception as e:
                logger.error("sentry_exception_capture_failed", error=str(e))

        # Always log the exception
        logger.error(
            "exception_captured",
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            context=context or {},
        )


# Global monitoring system instance
monitoring = MonitoringSystem()
