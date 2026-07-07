"""Memory provider abstraction for Rose."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Optional, Protocol, runtime_checkable

from langchain_core.messages import BaseMessage

from ai_companion.settings import settings


@runtime_checkable
class MemoryProvider(Protocol):
    """Protocol for Rose long-term memory operations."""

    name: str

    async def extract_and_store_memories(self, message: BaseMessage, session_id: Optional[str] = None) -> None:
        """Extract memory-worthy content from a message and persist it."""
        ...

    def get_relevant_memories(self, context: str, session_id: Optional[str] = None) -> list[str]:
        """Return relevant long-term memories for a conversation context."""
        ...

    def get_relevant_memory_records(self, context: str, session_id: Optional[str] = None) -> list[dict[str, Any]]:
        """Return relevant memories with category metadata preserved."""
        ...

    def format_memories_for_prompt(self, memories: list[str]) -> str:
        """Format memory strings for prompt injection."""
        ...

    def format_memory_records_for_prompt(self, memories: list[dict[str, Any]]) -> str:
        """Format category-aware memory records for prompt injection."""
        ...

    def export_memories_for_session(self, session_id: str) -> list[dict[str, Any]]:
        """Export session memories without embeddings or raw vectors."""
        ...

    def delete_memories_for_session(self, session_id: str) -> bool:
        """Delete session memories."""
        ...


class LongTermMemoryProvider:
    """Provider wrapper around the existing Qdrant-backed MemoryManager."""

    name = "long_term_memory"

    def __init__(self, manager: MemoryProvider | None = None) -> None:
        if manager is None:
            from ai_companion.modules.memory.long_term.memory_manager import get_memory_manager

            manager = get_memory_manager()
        self.manager = manager

    async def extract_and_store_memories(self, message: BaseMessage, session_id: Optional[str] = None) -> None:
        await self.manager.extract_and_store_memories(message, session_id=session_id)

    def get_relevant_memories(self, context: str, session_id: Optional[str] = None) -> list[str]:
        return self.manager.get_relevant_memories(context, session_id=session_id)

    def get_relevant_memory_records(self, context: str, session_id: Optional[str] = None) -> list[dict[str, Any]]:
        return self.manager.get_relevant_memory_records(context, session_id=session_id)

    def format_memories_for_prompt(self, memories: list[str]) -> str:
        return self.manager.format_memories_for_prompt(memories)

    def format_memory_records_for_prompt(self, memories: list[dict[str, Any]]) -> str:
        return self.manager.format_memory_records_for_prompt(memories)

    def export_memories_for_session(self, session_id: str) -> list[dict[str, Any]]:
        return self.manager.export_memories_for_session(session_id)

    def delete_memories_for_session(self, session_id: str) -> bool:
        return self.manager.delete_memories_for_session(session_id)


def create_memory_provider() -> MemoryProvider:
    """Create the configured memory provider."""
    provider = settings.MEMORY_PROVIDER.strip().lower()
    if provider in {"long_term", "long_term_memory", "qdrant"}:
        return LongTermMemoryProvider()
    raise ValueError(f"Unsupported MEMORY_PROVIDER '{settings.MEMORY_PROVIDER}'")


@lru_cache(maxsize=1)
def get_memory_provider() -> MemoryProvider:
    """Return the shared memory provider."""
    return create_memory_provider()
