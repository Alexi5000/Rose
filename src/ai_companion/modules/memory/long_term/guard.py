"""Guard to disable Qdrant memory searches temporarily when repeated internal errors are detected.

This module implements a lightweight in-memory guard to track the count of Qdrant
UnexpectedResponse (500) errors over a short window and temporarily disable
further searches for a configurable cooldown period to reduce error storms.
"""

import time
from collections import deque
from typing import Deque

DEFAULT_WINDOW_SECONDS = 60
DEFAULT_THRESHOLD = 3
DEFAULT_COOLDOWN_SECONDS = 60


class MemoryDegradationGuard:
    """In-memory guard that disables memory searches if repeated Qdrant errors occur.

    Simple implementation using timestamps and deque to avoid extra dependencies.
    """

    def __init__(self, window_seconds: int = DEFAULT_WINDOW_SECONDS, threshold: int = DEFAULT_THRESHOLD, cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS):
        self.window_seconds = window_seconds
        self.threshold = threshold
        self.cooldown_seconds = cooldown_seconds
        self.errors: Deque[float] = deque(maxlen=1000)
        self.disabled_until = 0.0

    def record_error(self) -> None:
        now = time.time()
        self.errors.append(now)
        self._evaluate(now)

    def _evaluate(self, now: float) -> None:
        # Remove errors outside the window
        while self.errors and now - self.errors[0] > self.window_seconds:
            self.errors.popleft()

        # If threshold exceeded, set cooldown
        if len(self.errors) >= self.threshold:
            self.disabled_until = now + self.cooldown_seconds

    def is_disabled(self) -> bool:
        return time.time() < self.disabled_until

    def reset(self) -> None:
        """Reset the guard by clearing all errors and re-enabling."""
        self.errors.clear()
        self.disabled_until = 0.0


# Module-level singleton guard
guard = MemoryDegradationGuard()
