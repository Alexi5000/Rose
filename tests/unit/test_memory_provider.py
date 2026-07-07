"""Unit tests for memory provider selection."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage

from ai_companion.modules.memory.provider import LongTermMemoryProvider, MemoryProvider, get_memory_provider
from ai_companion.settings import settings


def test_get_memory_provider_defaults_to_long_term(monkeypatch):
    monkeypatch.setattr(settings, "MEMORY_PROVIDER", "long_term")
    get_memory_provider.cache_clear()

    with patch("ai_companion.modules.memory.long_term.memory_manager.get_memory_manager") as mock_get_manager:
        provider = get_memory_provider()

    assert isinstance(provider, LongTermMemoryProvider)
    assert isinstance(provider, MemoryProvider)
    assert provider.name == "long_term_memory"
    mock_get_manager.assert_called_once()

    get_memory_provider.cache_clear()


def test_get_memory_provider_rejects_unknown_provider(monkeypatch):
    monkeypatch.setattr(settings, "MEMORY_PROVIDER", "unknown")
    get_memory_provider.cache_clear()

    with pytest.raises(ValueError, match="Unsupported MEMORY_PROVIDER"):
        get_memory_provider()

    get_memory_provider.cache_clear()


@pytest.mark.asyncio
async def test_long_term_memory_provider_delegates_to_manager():
    manager = MagicMock()
    manager.extract_and_store_memories = AsyncMock()
    manager.get_relevant_memories.return_value = ["User likes quiet rituals."]
    manager.get_relevant_memory_records.return_value = [
        {
            "text": "User likes quiet rituals.",
            "metadata": {"memory_type": "coping_practice", "sensitivity": "standard"},
        }
    ]
    manager.format_memories_for_prompt.return_value = "- User likes quiet rituals."
    manager.format_memory_records_for_prompt.return_value = "Coping practices:\n- User likes quiet rituals."
    manager.export_memories_for_session.return_value = [{"text": "memory", "metadata": {}}]
    manager.delete_memories_for_session.return_value = True

    provider = LongTermMemoryProvider(manager=manager)
    message = HumanMessage(content="I like quiet rituals.")

    await provider.extract_and_store_memories(message, session_id="session-123")

    manager.extract_and_store_memories.assert_awaited_once_with(message, session_id="session-123")
    assert provider.get_relevant_memories("ritual", session_id="session-123") == ["User likes quiet rituals."]
    assert provider.get_relevant_memory_records("ritual", session_id="session-123") == [
        {
            "text": "User likes quiet rituals.",
            "metadata": {"memory_type": "coping_practice", "sensitivity": "standard"},
        }
    ]
    assert provider.format_memories_for_prompt(["User likes quiet rituals."]) == "- User likes quiet rituals."
    assert (
        provider.format_memory_records_for_prompt(
            [
                {
                    "text": "User likes quiet rituals.",
                    "metadata": {"memory_type": "coping_practice", "sensitivity": "standard"},
                }
            ]
        )
        == "Coping practices:\n- User likes quiet rituals."
    )
    assert provider.export_memories_for_session("session-123") == [{"text": "memory", "metadata": {}}]
    assert provider.delete_memories_for_session("session-123") is True
