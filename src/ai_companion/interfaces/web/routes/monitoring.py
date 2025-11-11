"""Monitoring and metrics API endpoints.

This module provides endpoints for accessing monitoring data, metrics,
and alert information.
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ai_companion.core.logging_config import get_logger
from ai_companion.core.metrics import metrics
from ai_companion.core.monitoring import monitoring

logger = get_logger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


class MetricsResponse(BaseModel):
    """Response model for metrics endpoint."""

    counters: Dict[str, int]
    gauges: Dict[str, float]
    histograms: Dict[str, Dict[str, float]]
    timestamp: str


class MonitoringStatusResponse(BaseModel):
    """Response model for monitoring status endpoint."""

    sentry_enabled: bool
    alert_thresholds_count: int
    active_alerts_count: int
    last_evaluation: str
    active_alerts: list


class AlertResponse(BaseModel):
    """Response model for individual alert."""

    name: str
    severity: str
    message: str
    metric_value: float
    threshold: float
    timestamp: str


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(request: Request) -> MetricsResponse:
    """Get current application metrics.

    Returns:
        Current metrics including counters, gauges, and histograms

    Example:
        ```
        GET /api/monitoring/metrics
        ```
    """
    try:
        metrics_summary = metrics.get_metrics_summary()

        logger.info("metrics_retrieved", request_id=getattr(request.state, "request_id", None))

        return MetricsResponse(**metrics_summary)

    except Exception as e:
        logger.error("metrics_retrieval_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@router.get("/status", response_model=MonitoringStatusResponse)
async def get_monitoring_status(request: Request) -> MonitoringStatusResponse:
    """Get monitoring system status.

    Returns:
        Monitoring system status including alert configuration and active alerts

    Example:
        ```
        GET /api/monitoring/status
        ```
    """
    try:
        status = monitoring.get_monitoring_status()

        logger.info(
            "monitoring_status_retrieved",
            request_id=getattr(request.state, "request_id", None),
            active_alerts=status["active_alerts_count"],
        )

        return MonitoringStatusResponse(**status)

    except Exception as e:
        logger.error("monitoring_status_retrieval_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve monitoring status")


@router.get("/alerts", response_model=list[AlertResponse])
async def get_alerts(request: Request, hours: int = 24) -> list[AlertResponse]:
    """Get alert history.

    Args:
        hours: Number of hours of history to retrieve (default: 24)

    Returns:
        List of alerts from the specified time period

    Example:
        ```
        GET /api/monitoring/alerts?hours=24
        ```
    """
    try:
        if hours < 1 or hours > 168:  # Max 1 week
            raise HTTPException(status_code=400, detail="Hours must be between 1 and 168")

        alert_history = monitoring.get_alert_history(hours=hours)

        alerts = [
            AlertResponse(
                name=alert.name,
                severity=alert.severity,
                message=alert.message,
                metric_value=alert.metric_value,
                threshold=alert.threshold,
                timestamp=alert.timestamp.isoformat(),
            )
            for alert in alert_history
        ]

        logger.info(
            "alerts_retrieved", request_id=getattr(request.state, "request_id", None), count=len(alerts), hours=hours
        )

        return alerts

    except HTTPException:
        raise
    except Exception as e:
        logger.error("alerts_retrieval_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.post("/evaluate")
async def evaluate_thresholds(request: Request) -> Dict[str, Any]:
    """Manually trigger threshold evaluation.

    This endpoint allows manual triggering of alert threshold evaluation,
    useful for testing or on-demand monitoring checks.

    Returns:
        Dictionary with evaluation results

    Example:
        ```
        POST /api/monitoring/evaluate
        ```
    """
    try:
        triggered_alerts = monitoring.evaluate_thresholds()

        logger.info(
            "thresholds_evaluated",
            request_id=getattr(request.state, "request_id", None),
            triggered_count=len(triggered_alerts),
        )

        return {
            "evaluated": True,
            "triggered_alerts_count": len(triggered_alerts),
            "triggered_alerts": [
                {"name": alert.name, "severity": alert.severity, "message": alert.message} for alert in triggered_alerts
            ],
        }

    except Exception as e:
        logger.error("threshold_evaluation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to evaluate thresholds")
