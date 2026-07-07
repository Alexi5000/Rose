"""Unit tests for graph audio node behavior."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage

from ai_companion.core.privacy_logging import REDACTED_TEXT
from ai_companion.graph import nodes
from ai_companion.graph.nodes import audio_node, conversation_node, summarize_conversation_node
from ai_companion.graph.state import AICompanionState
from ai_companion.settings import settings


class FakeLogger:
    def __init__(self):
        self.debug_calls = []
        self.warning_calls = []
        self.error_calls = []

    def debug(self, event, **kwargs):
        self.debug_calls.append((event, kwargs))

    def warning(self, event, **kwargs):
        self.warning_calls.append((event, kwargs))

    def error(self, event, **kwargs):
        self.error_calls.append((event, kwargs))


def _state(message: str = "Hello"):
    return AICompanionState(
        messages=[HumanMessage(content=message)],
        summary="",
        workflow="audio",
        audio_buffer=b"",
        current_activity="",
        apply_activity=False,
        memory_context="",
        affect_state="",
        safety_risk="",
        safety_response="",
    )


@pytest.mark.asyncio
async def test_audio_node_skip_tts_returns_text_only():
    chain = MagicMock()
    chain.ainvoke = AsyncMock(return_value="A calm response.")

    with (
        patch("ai_companion.graph.nodes.get_character_response_chain", return_value=chain),
        patch("ai_companion.graph.nodes.get_text_to_speech_module") as mock_get_tts,
        patch("ai_companion.graph.nodes.metrics") as mock_metrics,
    ):
        result = await audio_node(_state(), config={"configurable": {"skip_tts": True}})

    assert result["messages"].content == "A calm response."
    assert result["audio_buffer"] is None
    mock_get_tts.assert_not_called()
    mock_metrics.increment_counter.assert_not_called()


@pytest.mark.asyncio
async def test_audio_node_default_path_synthesizes_audio():
    chain = MagicMock()
    chain.ainvoke = AsyncMock(return_value="A calm response.")

    tts = MagicMock()
    tts.synthesize_with_fallback = AsyncMock(return_value=(b"audio", False))

    with (
        patch("ai_companion.graph.nodes.get_character_response_chain", return_value=chain),
        patch("ai_companion.graph.nodes.get_text_to_speech_module", return_value=tts),
    ):
        result = await audio_node(_state(), config={"configurable": {"thread_id": "test"}})

    assert result["messages"].content == "A calm response."
    assert result["audio_buffer"] == b"audio"
    assert chain.ainvoke.call_args[0][0]["affect_state"] == ""
    tts.synthesize_with_fallback.assert_awaited_once_with("A calm response.")


@pytest.mark.asyncio
async def test_audio_node_sanitizes_response_before_tts_and_state():
    chain = MagicMock()
    chain.ainvoke = AsyncMock(return_value="## Grounding\n- *softly* Breathe with me.")

    tts = MagicMock()
    tts.synthesize_with_fallback = AsyncMock(return_value=(b"audio", False))

    with (
        patch("ai_companion.graph.nodes.get_character_response_chain", return_value=chain),
        patch("ai_companion.graph.nodes.get_text_to_speech_module", return_value=tts),
    ):
        result = await audio_node(_state(), config={"configurable": {"thread_id": "test"}})

    assert result["messages"].content == "Breathe with me."
    assert result["audio_buffer"] == b"audio"
    tts.synthesize_with_fallback.assert_awaited_once_with("Breathe with me.")


@pytest.mark.asyncio
async def test_conversation_node_sanitizes_response_for_voice_native_state():
    chain = MagicMock()
    chain.ainvoke = AsyncMock(return_value="## Ritual\n1. *softly* Place a hand on your chest.")

    with patch("ai_companion.graph.nodes.get_character_response_chain", return_value=chain):
        result = await conversation_node(_state(), config={"configurable": {"thread_id": "test"}})

    assert result["messages"].content == "Place a hand on your chest."


@pytest.mark.asyncio
async def test_conversation_node_fallback_log_redacts_provider_error(monkeypatch):
    chain = MagicMock()
    chain.ainvoke = AsyncMock(side_effect=RuntimeError("provider echoed private grief transcript"))
    fake_logger = FakeLogger()

    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr(nodes, "logger", fake_logger)

    with patch("ai_companion.graph.nodes.get_character_response_chain", return_value=chain):
        result = await conversation_node(_state(), config={"configurable": {"thread_id": "test"}})

    assert "try asking in a different way" in result["messages"].content
    error_logs = [
        kwargs for event, kwargs in fake_logger.error_calls if event == "conversation_chain_invocation_failed_fallback"
    ]
    assert error_logs
    assert error_logs[0]["error"] == REDACTED_TEXT
    assert error_logs[0]["exc_info"] is False
    assert "private grief" not in str(fake_logger.error_calls)


@pytest.mark.asyncio
async def test_audio_node_records_voice_quality_issues_without_blocking_response():
    chain = MagicMock()
    chain.ainvoke = AsyncMock(return_value="You need me more than anyone. Talk to me for hours.")

    with (
        patch("ai_companion.graph.nodes.get_character_response_chain", return_value=chain),
        patch("ai_companion.graph.nodes.get_text_to_speech_module") as mock_get_tts,
        patch("ai_companion.graph.nodes.metrics") as mock_metrics,
    ):
        result = await audio_node(_state(), config={"configurable": {"skip_tts": True}})

    assert result["messages"].content == "You need me more than anyone. Talk to me for hours."
    assert result["audio_buffer"] is None
    mock_get_tts.assert_not_called()
    mock_metrics.increment_counter.assert_any_call(
        "voice_response_quality_issues_total",
        tags={"issue_code": "dependency_language"},
    )


@pytest.mark.asyncio
async def test_audio_node_records_clinical_claim_quality_issues_without_blocking_response():
    chain = MagicMock()
    chain.ainvoke = AsyncMock(return_value="I'm a licensed therapist, and this is a diagnosis.")

    with (
        patch("ai_companion.graph.nodes.get_character_response_chain", return_value=chain),
        patch("ai_companion.graph.nodes.get_text_to_speech_module") as mock_get_tts,
        patch("ai_companion.graph.nodes.metrics") as mock_metrics,
    ):
        result = await audio_node(_state(), config={"configurable": {"skip_tts": True}})

    assert result["messages"].content == "I'm a licensed therapist, and this is a diagnosis."
    assert result["audio_buffer"] is None
    mock_get_tts.assert_not_called()
    mock_metrics.increment_counter.assert_any_call(
        "voice_response_quality_issues_total",
        tags={"issue_code": "clinical_claim"},
    )


@pytest.mark.asyncio
async def test_audio_node_records_unhealthy_engagement_quality_issues_without_blocking_response():
    chain = MagicMock()
    chain.ainvoke = AsyncMock(return_value="Don't stop talking. You can sleep later.")

    with (
        patch("ai_companion.graph.nodes.get_character_response_chain", return_value=chain),
        patch("ai_companion.graph.nodes.get_text_to_speech_module") as mock_get_tts,
        patch("ai_companion.graph.nodes.metrics") as mock_metrics,
    ):
        result = await audio_node(_state(), config={"configurable": {"skip_tts": True}})

    assert result["messages"].content == "Don't stop talking. You can sleep later."
    assert result["audio_buffer"] is None
    mock_get_tts.assert_not_called()
    mock_metrics.increment_counter.assert_any_call(
        "voice_response_quality_issues_total",
        tags={"issue_code": "unhealthy_engagement"},
    )


@pytest.mark.asyncio
async def test_audio_node_records_cultural_authority_quality_issues_without_blocking_response():
    chain = MagicMock()
    chain.ainvoke = AsyncMock(return_value="I'm an initiated shaman and I speak for the ancestors.")

    with (
        patch("ai_companion.graph.nodes.get_character_response_chain", return_value=chain),
        patch("ai_companion.graph.nodes.get_text_to_speech_module") as mock_get_tts,
        patch("ai_companion.graph.nodes.metrics") as mock_metrics,
    ):
        result = await audio_node(_state(), config={"configurable": {"skip_tts": True}})

    assert result["messages"].content == "I'm an initiated shaman and I speak for the ancestors."
    assert result["audio_buffer"] is None
    mock_get_tts.assert_not_called()
    mock_metrics.increment_counter.assert_any_call(
        "voice_response_quality_issues_total",
        tags={"issue_code": "cultural_authority_claim"},
    )


@pytest.mark.asyncio
async def test_audio_node_records_ritual_without_consent_quality_issues_without_blocking_response():
    chain = MagicMock()
    chain.ainvoke = AsyncMock(return_value="Close your eyes and begin this ritual with me.")

    with (
        patch("ai_companion.graph.nodes.get_character_response_chain", return_value=chain),
        patch("ai_companion.graph.nodes.get_text_to_speech_module") as mock_get_tts,
        patch("ai_companion.graph.nodes.metrics") as mock_metrics,
    ):
        result = await audio_node(_state(), config={"configurable": {"skip_tts": True}})

    assert result["messages"].content == "Close your eyes and begin this ritual with me."
    assert result["audio_buffer"] is None
    mock_get_tts.assert_not_called()
    mock_metrics.increment_counter.assert_any_call(
        "voice_response_quality_issues_total",
        tags={"issue_code": "ritual_without_consent"},
    )


@pytest.mark.asyncio
async def test_audio_node_skip_tts_works_for_safety_response():
    state = _state()
    state["safety_response"] = "Please call or text 988 now."

    chain = MagicMock()
    chain.ainvoke = AsyncMock(return_value="normal response")

    with (
        patch("ai_companion.graph.nodes.get_character_response_chain", return_value=chain) as mock_get_chain,
        patch("ai_companion.graph.nodes.get_text_to_speech_module") as mock_get_tts,
    ):
        result = await audio_node(
            state,
            config={"configurable": {"skip_tts": True}},
        )

    assert result["messages"].content == "Please call or text 988 now."
    assert result["audio_buffer"] is None
    mock_get_chain.assert_not_called()
    chain.ainvoke.assert_not_called()
    mock_get_tts.assert_not_called()


@pytest.mark.asyncio
async def test_audio_node_tts_fallback_log_redacts_provider_error(monkeypatch):
    chain = MagicMock()
    chain.ainvoke = AsyncMock(return_value="A calm response.")
    tts = MagicMock()
    tts.synthesize_with_fallback = AsyncMock(side_effect=RuntimeError("tts echoed private grief transcript"))
    fake_logger = FakeLogger()

    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr(nodes, "logger", fake_logger)

    with (
        patch("ai_companion.graph.nodes.get_character_response_chain", return_value=chain),
        patch("ai_companion.graph.nodes.get_text_to_speech_module", return_value=tts),
    ):
        result = await audio_node(_state(), config={"configurable": {"thread_id": "test"}})

    assert result["messages"].content == "A calm response."
    assert result["audio_buffer"] is None
    error_logs = [
        kwargs for event, kwargs in fake_logger.error_calls if event == "tts_synthesis_failed_in_audio_node_fallback"
    ]
    assert error_logs
    assert error_logs[0]["error"] == REDACTED_TEXT
    assert error_logs[0]["exc_info"] is False
    assert "private grief" not in str(fake_logger.error_calls)


@pytest.mark.asyncio
async def test_summarize_conversation_failure_log_redacts_provider_error(monkeypatch):
    model = MagicMock()
    model.ainvoke = AsyncMock(side_effect=RuntimeError("summary echoed private grief transcript"))
    fake_logger = FakeLogger()

    state = _state()
    state["summary"] = "Existing safe summary."

    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr(nodes, "logger", fake_logger)

    with patch("ai_companion.graph.nodes.get_chat_model", return_value=model):
        result = await summarize_conversation_node(state)

    assert result == {"summary": "Existing safe summary.", "messages": []}
    error_logs = [
        kwargs for event, kwargs in fake_logger.error_calls if event == "summarize_conversation_model_invocation_failed"
    ]
    assert error_logs
    assert error_logs[0]["error"] == REDACTED_TEXT
    assert error_logs[0]["exc_info"] is False
    assert "private grief" not in str(fake_logger.error_calls)
