"""Background scheduler for monitoring tasks.

This module provides a background scheduler that periodically evaluates
alert thresholds and performs monitoring tasks.
"""

import asyncio
from typing import Optional

from ai_companion.core.logging_config import get_logger
from ai_companion.core.monitoring import monitoring

logger = get_logger(__name__)


class MonitoringScheduler:
    """Background scheduler for monitoring tasks."""

    def __init__(self, evaluation_interval: int = 60):
        """Initialize monitoring scheduler.

        Args:
            evaluation_interval: Interval in seconds between evaluations (default: 60)
        """
        self.evaluation_interval = evaluation_interval
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start the monitoring scheduler."""
        if self._running:
            logger.warning("monitoring_scheduler_already_running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("monitoring_scheduler_started", evaluation_interval=self.evaluation_interval)

    async def stop(self) -> None:
        """Stop the monitoring scheduler."""
        if not self._running:
            return

        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("monitoring_scheduler_stopped")

    async def _run(self) -> None:
        """Run the monitoring scheduler loop."""
        while self._running:
            try:
                # Evaluate alert thresholds
                triggered_alerts = monitoring.evaluate_thresholds()

                if triggered_alerts:
                    logger.warning("monitoring_evaluation_completed", triggered_alerts=len(triggered_alerts))
                else:
                    logger.debug("monitoring_evaluation_completed", triggered_alerts=0)

            except Exception as e:
                logger.error("monitoring_evaluation_error", error=str(e), error_type=type(e).__name__)

            # Wait for next evaluation
            try:
                await asyncio.sleep(self.evaluation_interval)
            except asyncio.CancelledError:
                break


# Global scheduler instance
scheduler = MonitoringScheduler()
