from __future__ import annotations

import pytest

from ai_companion.core.privacy_logging import REDACTED_TEXT
from ai_companion.core.retry import async_retry_with_exponential_backoff, retry_with_exponential_backoff
from ai_companion.settings import settings


def test_sync_retry_logs_redacted_exception_by_default(monkeypatch, caplog) -> None:
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)

    @retry_with_exponential_backoff(max_retries=1)
    def fail_once():
        raise RuntimeError("provider echoed private grief payload")

    with caplog.at_level("WARNING", logger="ai_companion.core.retry"):
        with pytest.raises(RuntimeError):
            fail_once()

    assert "private grief" not in caplog.text
    assert REDACTED_TEXT in caplog.text
    assert "retry_attempt_failed" in caplog.text
    assert "retry_exhausted" in caplog.text


@pytest.mark.asyncio
async def test_async_retry_logs_redacted_exception_by_default(monkeypatch, caplog) -> None:
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)

    async def fail_once():
        raise RuntimeError("provider echoed private grief payload")

    with caplog.at_level("WARNING", logger="ai_companion.core.retry"):
        with pytest.raises(RuntimeError):
            await async_retry_with_exponential_backoff(fail_once, max_retries=1)

    assert "private grief" not in caplog.text
    assert REDACTED_TEXT in caplog.text
    assert "retry_attempt_failed" in caplog.text
    assert "retry_exhausted" in caplog.text
