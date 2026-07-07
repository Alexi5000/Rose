"""Unit tests for session memory privacy controls."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from langchain_core.messages import HumanMessage
from starlette.requests import Request

from ai_companion.core.privacy_logging import REDACTED_TEXT
from ai_companion.graph import nodes
from ai_companion.graph.nodes import memory_extraction_node, memory_injection_node
from ai_companion.graph.state import AICompanionState
from ai_companion.interfaces.web.routes.session import (
    SessionMemoryPreferencesRequest,
    export_session_memories,
    forget_session_memories,
    get_memory_preferences,
    start_session,
    update_memory_preferences,
)
from ai_companion.modules.memory.privacy import (
    clear_session_memory_preferences,
    get_session_memory_preference,
    is_long_term_memory_enabled,
    sanitize_exported_memory,
    set_session_memory_preference,
)
from ai_companion.settings import settings


def _state(message: str = "I want this to stay in this session only.") -> AICompanionState:
    return AICompanionState(
        messages=[HumanMessage(content=message)],
        summary="",
        workflow="conversation",
        audio_buffer=b"",
        current_activity="",
        apply_activity=False,
        memory_context="",
        safety_risk="",
        safety_response="",
    )


class FakeLogger:
    def __init__(self):
        self.warning_calls = []
        self.error_calls = []

    def warning(self, event, **kwargs):
        self.warning_calls.append((event, kwargs))

    def error(self, event, **kwargs):
        self.error_calls.append((event, kwargs))

    def debug(self, *args, **kwargs):
        pass


@pytest.fixture(autouse=True)
def reset_memory_preferences():
    clear_session_memory_preferences()
    yield
    clear_session_memory_preferences()


def test_memory_preference_defaults_to_enabled():
    preference = get_session_memory_preference("session-a")

    assert preference.memory_mode == "enabled"
    assert preference.long_term_memory_enabled is True
    assert is_long_term_memory_enabled("session-a") is True


def test_memory_preference_can_disable_long_term_memory_for_session():
    set_session_memory_preference("session-a", "session_only")

    assert is_long_term_memory_enabled("session-a") is False
    assert is_long_term_memory_enabled("session-b") is True


def test_sanitize_exported_memory_removes_vectors_and_raw_payloads_recursively():
    exported = sanitize_exported_memory(
        {
            "text": "User prefers quiet morning grounding.",
            "metadata": {
                "id": "mem-1",
                "session_id": "session-123",
                "user_id": "user-123",
                "embedding": [0.1, 0.2],
                "audio": "base64-audio",
                "transcript": "raw transcript text",
                "prompt": "full prompt text",
                "api_key": "provider-key",
                "authorization": "Bearer token",
                "cookie": "session-cookie",
                "nested": {
                    "vector": [0.3],
                    "thread_id": "thread-123",
                    "raw_audio": "base64-audio",
                    "provider_payload": {"secret": "payload"},
                    "refresh_token": "refresh",
                    "safe": "keep",
                },
                "history": [
                    {"raw_payload": {"audio": "base64"}, "label": "safe"},
                    {"embeddings": [0.4], "raw_transcript": "private", "jwt": "signed", "note": "also safe"},
                    {"conversation_history": ["private turn"], "summary": "safe summary"},
                ],
            },
        }
    )

    assert exported == {
        "text": "User prefers quiet morning grounding.",
        "metadata": {
            "nested": {"safe": "keep"},
            "history": [{"label": "safe"}, {"note": "also safe"}, {"summary": "safe summary"}],
        },
    }


@pytest.mark.asyncio
async def test_memory_extraction_skips_background_task_for_session_only():
    session_id = str(uuid.uuid4())
    set_session_memory_preference(session_id, "session_only")

    with patch("ai_companion.graph.nodes.asyncio.create_task") as mock_create_task:
        result = await memory_extraction_node(_state(), config={"configurable": {"thread_id": session_id}})

    assert result == {}
    mock_create_task.assert_not_called()


@pytest.mark.asyncio
async def test_memory_injection_skips_retrieval_for_session_only():
    session_id = str(uuid.uuid4())
    set_session_memory_preference(session_id, "session_only")

    with patch("ai_companion.graph.nodes.get_memory_module") as mock_get_memory_module:
        result = await memory_injection_node(_state(), config={"configurable": {"thread_id": session_id}})

    assert result == {"memory_context": ""}
    mock_get_memory_module.assert_not_called()


@pytest.mark.asyncio
async def test_memory_injection_formats_typed_memory_records_when_available():
    session_id = str(uuid.uuid4())
    memory = MagicMock()
    memory.get_relevant_memory_records.return_value = [
        {
            "text": "User prefers quiet ancestor language only when invited.",
            "metadata": {"memory_type": "cultural_preference", "sensitivity": "standard"},
        },
        {
            "text": "Grief spikes around anniversaries.",
            "metadata": {"memory_type": "emotional_note", "sensitivity": "sensitive"},
        },
    ]
    memory.format_memory_records_for_prompt.return_value = (
        "Cultural and spiritual preferences:\n"
        "- User prefers quiet ancestor language only when invited.\n\n"
        "Emotional notes:\n"
        "- Grief spikes around anniversaries. (sensitive)"
    )

    with patch("ai_companion.graph.nodes.get_memory_module", return_value=memory):
        result = await memory_injection_node(
            _state("Anniversaries feel heavy."),
            config={"configurable": {"thread_id": session_id}},
        )

    memory.get_relevant_memory_records.assert_called_once()
    memory.format_memory_records_for_prompt.assert_called_once_with(memory.get_relevant_memory_records.return_value)
    memory.get_relevant_memories.assert_not_called()
    assert "Cultural and spiritual preferences" in result["memory_context"]
    assert "Emotional notes" in result["memory_context"]


@pytest.mark.asyncio
async def test_memory_injection_retrieval_error_log_redacts_sensitive_exception(monkeypatch):
    session_id = str(uuid.uuid4())
    fake_logger = FakeLogger()
    memory = MagicMock()
    memory.get_relevant_memory_records.side_effect = RuntimeError("retrieval echoed private grief")

    monkeypatch.setattr(nodes, "logger", fake_logger)

    with patch("ai_companion.graph.nodes.get_memory_module", return_value=memory):
        result = await memory_injection_node(
            _state("Anniversaries feel heavy."),
            config={"configurable": {"thread_id": session_id}},
        )

    warning_logs = [
        kwargs for event, kwargs in fake_logger.warning_calls if event == "long_term_memory_retrieval_failed"
    ]
    assert result == {"memory_context": ""}
    assert warning_logs
    assert warning_logs[0]["error"] == REDACTED_TEXT
    assert warning_logs[0]["exc_info"] is False
    assert "private grief" not in str(fake_logger.warning_calls)


@pytest.mark.asyncio
async def test_session_start_uses_emotional_support_positioning():
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/session/start",
            "headers": [],
            "client": ("testclient", 50000),
        }
    )

    response = await start_session(request)

    assert response.session_id
    assert response.message == "Session initialized. Rose is ready for emotional support when you are."
    assert "healing journey" not in response.message.lower()
    assert "therapeutic" not in response.message.lower()


@pytest.mark.asyncio
async def test_session_memory_preference_routes_update_and_read_mode():
    session_id = str(uuid.uuid4())

    update_response = await update_memory_preferences(
        session_id,
        SessionMemoryPreferencesRequest(memory_mode="session_only"),
    )
    read_response = await get_memory_preferences(session_id)

    assert update_response.session_id == session_id
    assert update_response.memory_mode == "session_only"
    assert update_response.long_term_memory_enabled is False
    assert "will not store or retrieve memories" in update_response.message
    assert read_response.memory_mode == "session_only"
    assert read_response.long_term_memory_enabled is False


@pytest.mark.asyncio
async def test_session_memory_preference_routes_validate_session_id():
    with pytest.raises(HTTPException) as exc_info:
        await get_memory_preferences("not-a-uuid")

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_session_memory_export_route_returns_text_and_metadata_only():
    session_id = str(uuid.uuid4())
    manager = MagicMock()
    manager.export_memories_for_session.return_value = [
        {
            "text": "User prefers morning grounding.",
            "metadata": {
                "id": "mem-1",
                "session_id": session_id,
                "user_id": "user-123",
                "embedding": [0.1, 0.2],
                "nested": {"vector": [0.3], "thread_id": "thread-123", "safe": "keep"},
            },
        }
    ]

    with patch("ai_companion.interfaces.web.routes.session.get_memory_provider", return_value=manager):
        response = await export_session_memories(session_id)

    assert response.session_id == session_id
    assert response.memories == [
        {
            "text": "User prefers morning grounding.",
            "metadata": {"nested": {"safe": "keep"}},
        }
    ]
    assert "Exported 1 session memories" in response.message
    manager.export_memories_for_session.assert_called_once_with(session_id)


@pytest.mark.asyncio
async def test_session_memory_export_route_redacts_provider_failure(monkeypatch):
    session_id = str(uuid.uuid4())
    fake_logger = FakeLogger()
    manager = MagicMock()
    manager.export_memories_for_session.side_effect = RuntimeError("qdrant echoed private grief memory")

    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr("ai_companion.interfaces.web.routes.session.logger", fake_logger)

    with patch("ai_companion.interfaces.web.routes.session.get_memory_provider", return_value=manager):
        with pytest.raises(HTTPException) as exc_info:
            await export_session_memories(session_id)

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Could not export session memories right now."
    error_logs = [kwargs for event, kwargs in fake_logger.error_calls if event == "session_memory_export_failed"]
    assert error_logs
    assert error_logs[0]["error"] == REDACTED_TEXT
    assert error_logs[0]["session_log_id"] != session_id
    assert error_logs[0]["exc_info"] is False
    assert "private grief" not in str(fake_logger.error_calls)
    assert session_id not in str(fake_logger.error_calls)


@pytest.mark.asyncio
async def test_session_memory_forget_route_deletes_session_memories():
    session_id = str(uuid.uuid4())
    manager = MagicMock()
    manager.delete_memories_for_session.return_value = True

    with patch("ai_companion.interfaces.web.routes.session.get_memory_provider", return_value=manager):
        response = await forget_session_memories(session_id)

    assert response.session_id == session_id
    assert response.deleted is True
    assert "were deleted" in response.message
    manager.delete_memories_for_session.assert_called_once_with(session_id)


@pytest.mark.asyncio
async def test_session_memory_forget_route_redacts_provider_failure(monkeypatch):
    session_id = str(uuid.uuid4())
    fake_logger = FakeLogger()
    manager = MagicMock()
    manager.delete_memories_for_session.side_effect = RuntimeError("qdrant echoed private grief memory")

    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr("ai_companion.interfaces.web.routes.session.logger", fake_logger)

    with patch("ai_companion.interfaces.web.routes.session.get_memory_provider", return_value=manager):
        with pytest.raises(HTTPException) as exc_info:
            await forget_session_memories(session_id)

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Could not delete session memories right now."
    error_logs = [kwargs for event, kwargs in fake_logger.error_calls if event == "session_memory_forget_failed"]
    assert error_logs
    assert error_logs[0]["error"] == REDACTED_TEXT
    assert error_logs[0]["session_log_id"] != session_id
    assert error_logs[0]["exc_info"] is False
    assert "private grief" not in str(fake_logger.error_calls)
    assert session_id not in str(fake_logger.error_calls)
