"""Helpers for keeping sensitive user content out of logs by default."""

import hashlib

from ai_companion.settings import settings

REDACTED_TEXT = "[redacted]"
SESSION_LOG_PREFIX = "session:"


def sensitive_text_for_log(text: str | None, max_chars: int = 80) -> str:
    """Return a safe log value for user-authored or memory text."""

    if not settings.LOG_SENSITIVE_CONTENT:
        return REDACTED_TEXT

    if text is None:
        return ""

    normalized = " ".join(text.split())
    if len(normalized) <= max_chars:
        return normalized
    return f"{normalized[:max_chars]}..."


def session_id_for_log(session_id: str | None) -> str:
    """Return a stable, non-reversible session identifier for structured logs."""

    if not session_id:
        return f"{SESSION_LOG_PREFIX}unknown"

    digest = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:12]
    return f"{SESSION_LOG_PREFIX}{digest}"


def exception_message_for_log(exc: Exception, max_chars: int = 120) -> str:
    """Return a privacy-safe exception message for logs.

    Exception messages from providers and validation layers may include user text,
    prompts, or raw payload fragments. Keep the exception type in nearby log
    fields and redact the message unless sensitive logging is explicitly enabled.
    """

    return sensitive_text_for_log(str(exc), max_chars=max_chars)


def exc_info_for_log() -> bool:
    """Only include tracebacks when sensitive-content logging is enabled."""

    return settings.LOG_SENSITIVE_CONTENT
