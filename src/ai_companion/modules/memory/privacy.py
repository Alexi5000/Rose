"""Session-scoped memory privacy preferences.

These preferences are intentionally process-local for now: they give live
sessions a clear way to opt out of long-term memory while the persistence layer
evolves toward account-level consent, export, and deletion.
"""

from dataclasses import dataclass
from typing import Any, Literal

MemoryMode = Literal["enabled", "session_only"]

DEFAULT_MEMORY_MODE: MemoryMode = "enabled"
SENSITIVE_MEMORY_EXPORT_KEYS = frozenset(
    {
        "account_id",
        "access_token",
        "api_key",
        "auth_header",
        "authorization",
        "audio",
        "audio_buffer",
        "audio_bytes",
        "bearer_token",
        "cookie",
        "conversation",
        "conversation_history",
        "dense_vector",
        "embedding",
        "embeddings",
        "id",
        "input_text",
        "messages",
        "owner_id",
        "password",
        "payload",
        "prompt",
        "provider_payload",
        "raw_audio",
        "raw_audio_bytes",
        "raw_embedding",
        "raw_embeddings",
        "raw_payload",
        "raw_transcript",
        "raw_vector",
        "raw_vectors",
        "refresh_token",
        "secret",
        "session_id",
        "set_cookie",
        "sparse_vector",
        "thread_id",
        "transcript",
        "user_id",
        "vector",
        "vectors",
        "jwt",
    }
)


@dataclass(frozen=True)
class SessionMemoryPreference:
    """Memory preference for a single conversation session."""

    session_id: str
    memory_mode: MemoryMode = DEFAULT_MEMORY_MODE

    @property
    def long_term_memory_enabled(self) -> bool:
        """Whether this session may read/write long-term memories."""

        return self.memory_mode == "enabled"


_session_preferences: dict[str, SessionMemoryPreference] = {}


def get_session_memory_preference(session_id: str | None) -> SessionMemoryPreference:
    """Return the memory preference for a session.

    Missing or empty session IDs keep the existing default behavior so older
    tests and non-session graph invocations continue to work.
    """

    normalized_session_id = session_id or "default"
    return _session_preferences.get(
        normalized_session_id,
        SessionMemoryPreference(session_id=normalized_session_id, memory_mode=DEFAULT_MEMORY_MODE),
    )


def set_session_memory_preference(session_id: str, memory_mode: MemoryMode) -> SessionMemoryPreference:
    """Set the memory preference for a session."""

    preference = SessionMemoryPreference(session_id=session_id, memory_mode=memory_mode)
    _session_preferences[session_id] = preference
    return preference


def is_long_term_memory_enabled(session_id: str | None) -> bool:
    """Return whether long-term memory is enabled for a session."""

    return get_session_memory_preference(session_id).long_term_memory_enabled


def clear_session_memory_preferences() -> None:
    """Clear in-process preferences.

    This is primarily useful for tests and local development resets.
    """

    _session_preferences.clear()


def sanitize_memory_export_value(value: Any) -> Any:
    """Recursively remove vector/raw payload fields from exported memory metadata."""

    if isinstance(value, dict):
        return {
            key: sanitize_memory_export_value(item)
            for key, item in value.items()
            if str(key).strip().lower() not in SENSITIVE_MEMORY_EXPORT_KEYS
        }
    if isinstance(value, list):
        return [sanitize_memory_export_value(item) for item in value]
    return value


def sanitize_exported_memory(memory: dict[str, Any]) -> dict[str, Any]:
    """Return a memory export record safe for user-facing download/API responses."""

    return {
        "text": memory.get("text", ""),
        "metadata": sanitize_memory_export_value(memory.get("metadata", {})),
    }


def sanitize_exported_memories(memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sanitize a list of exported memories."""

    return [sanitize_exported_memory(memory) for memory in memories]
