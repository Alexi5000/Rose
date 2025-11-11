"""Tests for monitoring and alerting system."""

import pytest

from ai_companion.core.metrics import metrics
from ai_companion.core.monitoring import Alert, AlertThreshold, MonitoringSystem


class TestMetricsCollector:
    """Test metrics collection functionality."""

    def test_increment_counter(self):
        """Test counter increment."""
        initial_value = metrics._counters.get("test_counter", 0)
        metrics.increment_counter("test_counter", value=5)
        assert metrics._counters["test_counter"] == initial_value + 5

    def test_set_gauge(self):
        """Test gauge setting."""
        metrics.set_gauge("test_gauge", 42.5)
        assert metrics._gauges["test_gauge"] == 42.5

    def test_record_histogram(self):
        """Test histogram recording."""
        metrics.record_histogram("test_histogram", 100.0)
        assert 100.0 in metrics._histograms["test_histogram"]

    def test_record_session_started(self):
        """Test session start recording."""
        initial_count = metrics._counters.get("sessions_started", 0)
        metrics.record_session_started("test_session_123")
        assert metrics._counters["sessions_started"] == initial_count + 1

    def test_record_api_call(self):
        """Test API call recording."""
        initial_success = metrics._counters.get("api_calls_groq_success", 0)
        metrics.record_api_call("groq", success=True, duration_ms=250.5)
        assert metrics._counters["api_calls_groq_success"] == initial_success + 1

    def test_get_metrics_summary(self):
        """Test metrics summary generation."""
        summary = metrics.get_metrics_summary()
        assert "counters" in summary
        assert "gauges" in summary
        assert "histograms" in summary
        assert "timestamp" in summary


class TestMonitoringSystem:
    """Test monitoring and alerting functionality."""

    def test_alert_threshold_creation(self):
        """Test alert threshold creation."""
        threshold = AlertThreshold(name="test_alert", metric_name="test_metric", threshold=10.0, comparison="gt")
        assert threshold.name == "test_alert"
        assert threshold.metric_name == "test_metric"
        assert threshold.threshold == 10.0
        assert threshold.enabled is True

    def test_alert_creation(self):
        """Test alert creation."""
        from datetime import datetime

        alert = Alert(
            name="test_alert",
            message="Test alert message",
            severity="critical",
            metric_value=15.0,
            threshold=10.0,
            timestamp=datetime.utcnow(),
        )
        assert alert.name == "test_alert"
        assert alert.severity == "critical"
        assert alert.metric_value == 15.0

    def test_monitoring_system_initialization(self):
        """Test monitoring system initialization."""
        monitor = MonitoringSystem()
        assert len(monitor._alert_thresholds) > 0  # Default thresholds added
        assert monitor._sentry_enabled is False  # No DSN configured in tests

    def test_add_threshold(self):
        """Test adding custom threshold."""
        monitor = MonitoringSystem()
        initial_count = len(monitor._alert_thresholds)

        threshold = AlertThreshold(name="custom_alert", metric_name="custom_metric", threshold=50.0)
        monitor.add_threshold(threshold)

        assert len(monitor._alert_thresholds) == initial_count + 1

    def test_check_threshold_greater_than(self):
        """Test threshold checking with greater than comparison."""
        monitor = MonitoringSystem()
        threshold = AlertThreshold(name="test", metric_name="test", threshold=10.0, comparison="gt")

        assert monitor._check_threshold(15.0, threshold) is True
        assert monitor._check_threshold(10.0, threshold) is False
        assert monitor._check_threshold(5.0, threshold) is False

    def test_check_threshold_less_than(self):
        """Test threshold checking with less than comparison."""
        monitor = MonitoringSystem()
        threshold = AlertThreshold(name="test", metric_name="test", threshold=10.0, comparison="lt")

        assert monitor._check_threshold(5.0, threshold) is True
        assert monitor._check_threshold(10.0, threshold) is False
        assert monitor._check_threshold(15.0, threshold) is False

    def test_get_alert_severity(self):
        """Test alert severity determination."""
        monitor = MonitoringSystem()

        assert monitor._get_alert_severity("high_error_rate") == "critical"
        assert monitor._get_alert_severity("high_memory_usage") == "critical"
        assert monitor._get_alert_severity("slow_response_time") == "warning"

    def test_format_alert_message(self):
        """Test alert message formatting."""
        monitor = MonitoringSystem()
        threshold = AlertThreshold(name="test_alert", metric_name="test_metric", threshold=10.0)

        message = monitor._format_alert_message(threshold, 15.5)
        assert "test_alert" in message
        assert "test_metric" in message
        assert "15.50" in message
        assert "10.00" in message

    def test_get_monitoring_status(self):
        """Test monitoring status retrieval."""
        monitor = MonitoringSystem()
        status = monitor.get_monitoring_status()

        assert "sentry_enabled" in status
        assert "alert_thresholds_count" in status
        assert "active_alerts_count" in status
        assert "last_evaluation" in status
        assert "active_alerts" in status

    def test_get_active_alerts(self):
        """Test active alerts retrieval."""
        monitor = MonitoringSystem()
        alerts = monitor.get_active_alerts()
        assert isinstance(alerts, list)

    def test_get_alert_history(self):
        """Test alert history retrieval."""
        monitor = MonitoringSystem()
        history = monitor.get_alert_history(hours=24)
        assert isinstance(history, list)


@pytest.mark.asyncio
class TestMonitoringScheduler:
    """Test monitoring scheduler functionality."""

    async def test_scheduler_start_stop(self):
        """Test scheduler start and stop."""
        from ai_companion.core.monitoring_scheduler import MonitoringScheduler

        scheduler = MonitoringScheduler(evaluation_interval=1)
        assert scheduler._running is False

        await scheduler.start()
        assert scheduler._running is True

        await scheduler.stop()
        assert scheduler._running is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
