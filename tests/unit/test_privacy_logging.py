"""Tests for privacy-preserving log helpers."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ai_companion.core import metrics as metrics_module
from ai_companion.core.exceptions import TextToSpeechError
from ai_companion.core.privacy_logging import (
    REDACTED_TEXT,
    exc_info_for_log,
    exception_message_for_log,
    sensitive_text_for_log,
    session_id_for_log,
)
from ai_companion.interfaces.web.routes import session as session_routes
from ai_companion.interfaces.web.routes import voice
from ai_companion.modules.memory.hierarchical import HierarchicalMemoryManager, SessionMemory, WorkingMemory
from ai_companion.modules.speech import speech_to_text, text_to_speech
from ai_companion.modules.speech.speech_to_text import SpeechToText
from ai_companion.modules.speech.text_to_speech import TextToSpeech
from ai_companion.settings import settings

VOICE_ROUTE_PATH = Path(voice.__file__)


class FakeLogger:
    def __init__(self):
        self.info_calls = []
        self.debug_calls = []
        self.warning_calls = []
        self.error_calls = []

    def info(self, event, **kwargs):
        self.info_calls.append((event, kwargs))

    def debug(self, event, **kwargs):
        self.debug_calls.append((event, kwargs))

    def warning(self, event, **kwargs):
        self.warning_calls.append((event, kwargs))

    def error(self, event, *args, **kwargs):
        self.error_calls.append((event, args, kwargs))


def test_http_voice_route_runtime_text_is_ascii():
    """Active voice API logs and comments should render cleanly in plain terminals."""

    text = VOICE_ROUTE_PATH.read_text(encoding="utf-8")

    assert text.isascii()
    assert "workflow_execution_failed" in text
    assert "audio_save_failed" in text
    assert "voice_processing_complete" in text
    assert "emoji" not in text


def test_session_id_for_log_is_stable_and_non_reversible():
    session_id = "123e4567-e89b-12d3-a456-426614174000"

    first = session_id_for_log(session_id)
    second = session_id_for_log(session_id)

    assert first == second
    assert first.startswith("session:")
    assert session_id not in first
    assert session_id_for_log(None) == "session:unknown"


def test_metrics_logs_do_not_emit_raw_session_id(monkeypatch):
    session_id = "123e4567-e89b-12d3-a456-426614174000"
    fake_logger = FakeLogger()
    collector = metrics_module.MetricsCollector()

    monkeypatch.setattr(metrics_module, "logger", fake_logger)

    collector.record_session_started(session_id)
    collector.record_voice_request(session_id, 2048)
    collector.record_workflow_execution(session_id, 123.4, success=True)

    assert session_id not in str(fake_logger.info_calls)
    session_logs = [kwargs for _, kwargs in fake_logger.info_calls if "session_log_id" in kwargs]
    assert len(session_logs) == 3
    assert {kwargs["session_log_id"] for kwargs in session_logs} == {session_id_for_log(session_id)}


@pytest.mark.asyncio
async def test_session_memory_routes_log_hashed_session_id(monkeypatch):
    session_id = "123e4567-e89b-12d3-a456-426614174000"
    fake_logger = FakeLogger()
    memory_provider = MagicMock()
    memory_provider.delete_memories_for_session.return_value = True

    monkeypatch.setattr(session_routes, "logger", fake_logger)
    monkeypatch.setattr(session_routes, "get_memory_provider", lambda: memory_provider)

    await session_routes.update_memory_preferences(
        session_id,
        session_routes.SessionMemoryPreferencesRequest(memory_mode="session_only"),
    )
    await session_routes.forget_session_memories(session_id)

    assert session_id not in str(fake_logger.info_calls)
    session_logs = [kwargs for _, kwargs in fake_logger.info_calls if "session_log_id" in kwargs]
    assert session_logs
    assert {kwargs["session_log_id"] for kwargs in session_logs} == {session_id_for_log(session_id)}


def test_sensitive_text_for_log_redacts_by_default(monkeypatch):
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)

    assert sensitive_text_for_log("I am grieving and scared") == REDACTED_TEXT


def test_sensitive_text_for_log_allows_local_opt_in_preview(monkeypatch):
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", True)

    assert sensitive_text_for_log("  I am grieving   and scared  ", max_chars=14) == "I am grieving ..."


def test_exception_message_for_log_redacts_by_default(monkeypatch):
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)

    exc = ValueError("provider echoed my private grief transcript")

    assert exception_message_for_log(exc) == REDACTED_TEXT
    assert exc_info_for_log() is False


def test_exception_message_for_log_allows_local_opt_in(monkeypatch):
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", True)

    exc = ValueError("provider echoed my private grief transcript")

    assert exception_message_for_log(exc, max_chars=24) == "provider echoed my priva..."
    assert exc_info_for_log() is True


@pytest.mark.asyncio
async def test_transcription_log_redacts_user_text_by_default(monkeypatch):
    class FakeSTT:
        name = "fake_stt"

        async def transcribe(self, audio_data):
            return "I am grieving and scared"

    fake_logger = FakeLogger()
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr(voice, "logger", fake_logger)

    transcript = await voice._transcribe_audio(b"audio-bytes", "session-1", FakeSTT())

    assert transcript == "I am grieving and scared"
    transcription_logs = [kwargs for event, kwargs in fake_logger.info_calls if event == "transcription_complete"]
    assert transcription_logs
    assert transcription_logs[0]["text"] == REDACTED_TEXT
    assert transcription_logs[0]["text_length"] == len(transcript)
    assert transcription_logs[0]["session_log_id"] == session_id_for_log("session-1")
    assert "session-1" not in str(fake_logger.info_calls)


@pytest.mark.asyncio
async def test_speech_to_text_success_log_redacts_transcript(monkeypatch):
    class FakeGroq:
        def __init__(self, *args, **kwargs):
            self.audio = type("Audio", (), {})()
            self.audio.transcriptions = type("Transcriptions", (), {})()
            self.audio.transcriptions.create = lambda **_: "My grief feels sharp tonight"

    fake_logger = FakeLogger()
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr(speech_to_text, "logger", fake_logger)
    monkeypatch.setattr(speech_to_text, "Groq", FakeGroq)

    stt = SpeechToText()
    transcript = await stt.transcribe(b"RIFF\x00\x00\x00\x00WAVE" + b"\x00" * 32)

    assert transcript == "My grief feels sharp tonight"
    success_logs = [event for event, _ in fake_logger.info_calls if event.startswith("Transcription successful")]
    assert success_logs
    assert "My grief" not in success_logs[0]
    assert REDACTED_TEXT in success_logs[0]


@pytest.mark.asyncio
async def test_tts_validation_log_redacts_text(monkeypatch):
    class FakeCircuitBreaker:
        async def call_async(self, fn):
            raise ValueError("provider-side validation failed")

    fake_logger = FakeLogger()
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr(text_to_speech, "logger", fake_logger)

    tts = TextToSpeech()
    tts._circuit_breaker = FakeCircuitBreaker()

    with pytest.raises(ValueError):
        await tts.synthesize("Please hold my grief gently")

    error_events = [event for event, _, _ in fake_logger.error_calls]
    assert error_events
    assert "Please hold" not in error_events[0]
    assert REDACTED_TEXT in error_events[0]


def test_hierarchical_memory_summary_log_redacts_sensitive_text_by_default(monkeypatch, caplog):
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)

    session_memory = SessionMemory(session_id="session-privacy")

    with caplog.at_level("DEBUG", logger="ai_companion.modules.memory.hierarchical"):
        session_memory.update_summary("My grief about my father feels private tonight")

    assert "My grief" not in caplog.text
    assert REDACTED_TEXT in caplog.text


def test_hierarchical_memory_conflict_log_redacts_sensitive_facts_by_default(monkeypatch, caplog):
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)

    manager = HierarchicalMemoryManager(session_id="session-privacy")

    with caplog.at_level("INFO", logger="ai_companion.modules.memory.hierarchical"):
        conflict = manager.detect_conflict(
            "I do not live with my sister anymore",
            ["I live with my sister in Denver"],
        )

    assert conflict == "I live with my sister in Denver"
    assert "sister" not in caplog.text
    assert "Denver" not in caplog.text
    assert REDACTED_TEXT in caplog.text


def test_working_memory_emotion_log_redacts_arbitrary_labels_by_default(monkeypatch, caplog):
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)

    working_memory = WorkingMemory()

    with caplog.at_level("DEBUG", logger="ai_companion.modules.memory.hierarchical"):
        working_memory.update_emotion("ashamed about my divorce")

    assert "divorce" not in caplog.text
    assert REDACTED_TEXT in caplog.text


@pytest.mark.asyncio
async def test_tts_route_error_does_not_embed_generated_response(monkeypatch):
    class FakeTTS:
        name = "fake_tts"

        async def synthesize_cached(self, response_text):
            raise RuntimeError("provider unavailable")

    sensitive_response = "Your private grief about your sister can be held gently."

    with pytest.raises(TextToSpeechError) as exc_info:
        await voice._generate_audio_response(sensitive_response, "session-privacy", FakeTTS())

    error_text = str(exc_info.value)
    assert "sister" not in error_text
    assert "private grief" not in error_text
    assert "having trouble generating the audio" in error_text


def test_voice_api_call_failure_log_redacts_provider_error(monkeypatch):
    fake_logger = FakeLogger()
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr(voice, "logger", fake_logger)

    with pytest.raises(ValueError):
        with voice.track_api_call("fake_provider", "session-privacy"):
            raise ValueError("provider echoed my private grief transcript")

    failure_logs = [kwargs for event, _, kwargs in fake_logger.error_calls if event == "service_failed"]
    assert failure_logs
    assert failure_logs[0]["error"] == REDACTED_TEXT
    assert failure_logs[0]["session_log_id"] == session_id_for_log("session-privacy")
    assert failure_logs[0]["marker"] == "error"
    assert "emoji" not in failure_logs[0]
    assert failure_logs[0]["exc_info"] is False
    assert "session-privacy" not in str(fake_logger.error_calls)


@pytest.mark.asyncio
async def test_workflow_failure_log_redacts_exception_and_input_text(monkeypatch):
    class FakeGraph:
        async def ainvoke(self, *args, **kwargs):
            raise RuntimeError("provider echoed private grief transcript")

    fake_logger = FakeLogger()
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr(voice, "logger", fake_logger)

    with pytest.raises(Exception):
        await voice._process_workflow("I am grieving and scared", "session-privacy", FakeGraph())

    failure_logs = [kwargs for event, _, kwargs in fake_logger.error_calls if event == "workflow_execution_failed"]
    assert failure_logs
    assert failure_logs[0]["error"] == REDACTED_TEXT
    assert failure_logs[0]["input_text"] == REDACTED_TEXT
    assert failure_logs[0]["session_log_id"] == session_id_for_log("session-privacy")
    assert failure_logs[0]["exc_info"] is False
    assert "session-privacy" not in str(fake_logger.error_calls)
    assert "private grief" not in str(fake_logger.error_calls)
    assert "grieving and scared" not in str(fake_logger.error_calls)


@pytest.mark.asyncio
async def test_audio_save_failure_log_redacts_exception(monkeypatch, tmp_path):
    fake_logger = FakeLogger()
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr(voice, "logger", fake_logger)
    monkeypatch.setattr(
        voice.os, "open", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("path leaked private grief"))
    )

    with pytest.raises(Exception):
        await voice._save_audio_file(b"audio", "session-privacy", tmp_path)

    failure_logs = [kwargs for event, _, kwargs in fake_logger.error_calls if event == "audio_save_failed"]
    assert failure_logs
    assert failure_logs[0]["error"] == REDACTED_TEXT
    assert failure_logs[0]["session_log_id"] == session_id_for_log("session-privacy")
    assert "session-privacy" not in str(fake_logger.error_calls)
    assert "private grief" not in str(fake_logger.error_calls)


@pytest.mark.asyncio
async def test_audio_save_success_log_omits_temp_path_and_raw_session(monkeypatch, tmp_path):
    fake_logger = FakeLogger()
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr(voice, "logger", fake_logger)

    audio_url = await voice._save_audio_file(b"audio", "session-privacy", tmp_path)

    save_logs = [kwargs for event, kwargs in fake_logger.info_calls if event == "audio_file_saved"]
    assert save_logs
    assert "path" not in save_logs[0]
    assert save_logs[0]["session_log_id"] == session_id_for_log("session-privacy")
    assert audio_url.startswith(f"{voice.AUDIO_SERVE_PATH}/")
    assert "session-privacy" not in audio_url
    assert "session-privacy" not in str(fake_logger.info_calls)
    assert str(tmp_path) not in str(fake_logger.info_calls)


@pytest.mark.asyncio
async def test_stream_tts_error_log_redacts_exception(monkeypatch):
    class FakeTTS:
        async def synthesize_streaming(self, text):
            raise RuntimeError("tts streamed private grief")
            yield b""

    fake_logger = FakeLogger()
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr(voice, "logger", fake_logger)

    stream_tts_impl = voice.stream_tts.__wrapped__
    response = await stream_tts_impl(
        request=None,
        text="Please hold my grief",
        session_id="session-privacy",
        tts=FakeTTS(),
    )
    chunks = [chunk async for chunk in response.body_iterator]

    assert chunks == []
    failure_logs = [kwargs for event, _, kwargs in fake_logger.error_calls if event == "stream_tts_error"]
    assert failure_logs
    assert failure_logs[0]["error"] == REDACTED_TEXT
    assert failure_logs[0]["session_log_id"] == session_id_for_log("session-privacy")
    assert "session-privacy" not in str(fake_logger.error_calls)
    assert "private grief" not in str(fake_logger.error_calls)
