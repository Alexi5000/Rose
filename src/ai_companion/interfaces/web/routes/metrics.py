"""Metrics endpoints for monitoring and observability."""

from typing import Dict

from fastapi import APIRouter, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from ai_companion.core.logging_config import get_logger
from ai_companion.core.metrics import metrics

logger = get_logger(__name__)

router = APIRouter()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


class MetricsResponse(BaseModel):
    """Response model for metrics endpoint.

    Attributes:
        counters: Counter metrics (sessions, requests, errors)
        gauges: Gauge metrics (current values)
        histograms: Histogram metrics with statistics
        timestamp: ISO timestamp of metrics snapshot
    """

    counters: Dict[str, int]
    gauges: Dict[str, float]
    histograms: Dict[str, Dict[str, float]]
    timestamp: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "counters": {"sessions_started": 42, "voice_requests_total": 156, "errors_total": 3},
                    "gauges": {},
                    "histograms": {
                        "voice_audio_size_bytes": {"count": 156, "min": 12345, "max": 987654, "avg": 456789}
                    },
                    "timestamp": "2025-10-21T12:34:56.789Z",
                }
            ]
        }
    }


@router.get("/metrics", response_model=MetricsResponse)
@limiter.limit("60/minute")  # Higher limit for metrics scraping
async def get_metrics(request: Request) -> MetricsResponse:
    """Get application metrics for monitoring.

    Returns collected metrics including:
    - Session counts
    - Request counts by endpoint
    - Error counts by type
    - API call statistics
    - Performance histograms

    **Validation Rules:**
    - No authentication required (consider adding in production)
    - Rate limit: 60 requests per minute per IP address
    - Response time: Typically <100ms

    **Metrics Categories:**
    - Counters: Cumulative counts (sessions, requests, errors)
    - Gauges: Current values (active connections, memory usage)
    - Histograms: Statistical distributions (response times, audio sizes)

    Args:
        request: FastAPI request object (injected)

    Returns:
        MetricsResponse: Application metrics snapshot

    Raises:
        HTTPException 429: Rate limit exceeded (60 requests/minute)
    """
    logger.info("metrics_requested")

    summary = metrics.get_metrics_summary()

    return MetricsResponse(
        counters=summary["counters"],
        gauges=summary["gauges"],
        histograms=summary["histograms"],
        timestamp=summary["timestamp"],
    )
