"""Unit tests for WebSocket voice session processing."""

import asyncio
import json
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage, AIMessageChunk

from ai_companion.core.privacy_logging import REDACTED_TEXT, session_id_for_log
from ai_companion.interfaces.web.routes import voice_websocket as ws
from ai_companion.settings import settings


class FakeWebSocket:
    def __init__(self, graph):
        self.sent_json = []
        self.sent_bytes = []
        self.app = SimpleNamespace(state=SimpleNamespace(compiled_graph=graph))

    async def send_json(self, message):
        self.sent_json.append(message)

    async def send_bytes(self, data):
        self.sent_bytes.append(data)


class RouteFakeWebSocket(FakeWebSocket):
    def __init__(self, graph, incoming):
        super().__init__(graph)
        self.incoming = list(incoming)
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def receive(self):
        if not self.incoming:
            return {"type": "websocket.disconnect"}
        message = self.incoming.pop(0)
        delay = message.pop("delay", 0)
        if delay:
            await asyncio.sleep(delay)
        return message


class FakeLogger:
    def __init__(self):
        self.info_calls = []
        self.debug_calls = []
        self.warning_calls = []
        self.error_calls = []

    def warning(self, event, **kwargs):
        self.warning_calls.append((event, kwargs))

    def error(self, event, **kwargs):
        self.error_calls.append((event, kwargs))

    def info(self, event, **kwargs):
        self.info_calls.append((event, kwargs))

    def debug(self, event, **kwargs):
        self.debug_calls.append((event, kwargs))


class FakeGraph:
    def __init__(self, response_text="Rose response"):
        self.response_text = response_text
        self.payloads = []
        self.configs = []

    async def ainvoke(self, payload, config):
        self.payloads.append(payload)
        self.configs.append(config)
        return {"messages": [AIMessage(content=self.response_text)]}


class StreamingFakeGraph(FakeGraph):
    def __init__(self, deltas):
        super().__init__(response_text="")
        self.deltas = deltas
        self.ainvoke_called = False

    async def ainvoke(self, payload, config):
        self.ainvoke_called = True
        return await super().ainvoke(payload, config)

    async def astream_events(self, payload, config, version):
        self.payloads.append(payload)
        self.configs.append(config)
        for delta in self.deltas:
            yield {
                "event": "on_chat_model_stream",
                "metadata": {"langgraph_node": "audio_node"},
                "data": {"chunk": AIMessageChunk(content=delta)},
            }


class EmptyStreamingFakeGraph(FakeGraph):
    async def astream_events(self, payload, config, version):
        self.payloads.append(payload)
        self.configs.append(config)
        if False:
            yield {}


class SensitiveFailingStreamingGraph(FakeGraph):
    async def astream_events(self, payload, config, version):
        self.payloads.append(payload)
        self.configs.append(config)
        raise RuntimeError("llm stream echoed private grief transcript")
        if False:
            yield {}


class FakeTTS:
    def __init__(self, interrupt_session=None):
        self.texts = []
        self.interrupt_session = interrupt_session

    async def synthesize_streaming(self, text):
        self.texts.append(text)
        yield f"audio:{text}".encode()
        if self.interrupt_session is not None:
            self.interrupt_session.handle_interrupt()

    async def synthesize(self, text):
        return f"fallback:{text}".encode()


class SlowTTS(FakeTTS):
    async def synthesize_streaming(self, text):
        self.texts.append(text)
        await asyncio.sleep(0.05)
        yield f"audio:{text}".encode()


class FailingTTS:
    async def synthesize_streaming(self, text):
        raise RuntimeError("streaming tts failed")
        yield b""

    async def synthesize(self, text):
        raise RuntimeError("full tts failed")


class SensitiveFailingTTS:
    async def synthesize_streaming(self, text):
        raise RuntimeError("provider echoed private grief transcript")
        yield b""

    async def synthesize(self, text):
        raise RuntimeError("fallback echoed private grief transcript")


class StreamingSTT:
    name = "streaming_stt"
    supports_streaming = True

    def __init__(self):
        self.transcribe_called = False

    async def transcribe(self, audio_data, audio_format=None):
        self.transcribe_called = True
        return "I need support today."

    async def transcribe_streaming(self, audio_stream):
        chunks = []
        async for chunk in audio_stream:
            chunks.append(chunk)
            if len(chunks) == 1:
                yield "partial transcript"
        yield "I need support today."


class EmptyStreamingSTT(StreamingSTT):
    async def transcribe_streaming(self, audio_stream):
        async for _chunk in audio_stream:
            pass


class SensitiveFailingStreamingSTT(StreamingSTT):
    async def transcribe_streaming(self, audio_stream):
        async for _chunk in audio_stream:
            raise RuntimeError("streaming stt echoed private grief transcript")
        if False:
            yield ""


class BatchSTT:
    name = "groq_stt"
    supports_streaming = False

    def __init__(self, transcript="I need support today."):
        self.transcribed_audio = None
        self.transcript = transcript

    async def transcribe(self, audio_data, audio_format=None):
        self.transcribed_audio = audio_data
        return self.transcript

    async def transcribe_streaming(self, audio_stream):
        raise AssertionError("batch provider should not use streaming")


class SensitiveFailingSTT(BatchSTT):
    async def transcribe(self, audio_data, audio_format=None):
        raise RuntimeError("stt echoed private grief transcript")


def _json_messages(fake_websocket, msg_type):
    return [message for message in fake_websocket.sent_json if message["type"] == msg_type]


@pytest.mark.asyncio
async def test_websocket_route_handles_interrupt_while_processing_task_is_active(monkeypatch):
    stt = BatchSTT()
    tts = SlowTTS()
    recorded = []

    monkeypatch.setattr(ws, "get_stt", lambda: stt)
    monkeypatch.setattr(ws, "get_tts", lambda: tts)
    monkeypatch.setattr(ws.metrics, "record_histogram", lambda name, value, tags=None: recorded.append(name))

    fake_websocket = RouteFakeWebSocket(
        FakeGraph(),
        [
            {"type": "websocket.receive", "text": json.dumps({"type": ws.MSG_START_LISTENING})},
            {"type": "websocket.receive", "bytes": b"x" * 1200},
            {"type": "websocket.receive", "text": json.dumps({"type": ws.MSG_STOP_LISTENING})},
            {"type": "websocket.receive", "text": json.dumps({"type": ws.MSG_INTERRUPT}), "delay": 0.01},
            {"type": "websocket.disconnect", "delay": 0.01},
        ],
    )

    await ws.voice_websocket(fake_websocket, session_id="session-route-interrupt")

    audio_end_messages = _json_messages(fake_websocket, ws.MSG_AUDIO_END)
    assert fake_websocket.accepted is True
    assert audio_end_messages
    assert audio_end_messages[0]["interrupted"] is True
    assert "timings" in audio_end_messages[0]
    assert "ws_voice_turn_total_ms" in recorded
    assert fake_websocket.sent_bytes == []


@pytest.mark.asyncio
async def test_websocket_session_interrupt_cancels_active_processing_task(monkeypatch):
    monkeypatch.setattr(ws, "get_stt", lambda: BatchSTT())
    monkeypatch.setattr(ws, "get_tts", lambda: FakeTTS())

    fake_websocket = FakeWebSocket(FakeGraph())
    session = ws.VoiceWebSocketSession(fake_websocket, "session-cancel-processing")
    session.processing_task = asyncio.create_task(asyncio.sleep(10))

    session.handle_interrupt()
    await asyncio.sleep(0)

    assert session.interrupted is True
    assert session.processing_task.cancelled() is True


@pytest.mark.asyncio
async def test_websocket_streaming_stt_sends_partial_and_final_transcripts(monkeypatch):
    stt = StreamingSTT()
    monkeypatch.setattr(ws, "get_stt", lambda: stt)
    monkeypatch.setattr(ws, "get_tts", lambda: FakeTTS())

    fake_websocket = FakeWebSocket(FakeGraph())
    session = ws.VoiceWebSocketSession(fake_websocket, "session-1")

    session.start_listening_turn()
    await session.append_audio_chunk(b"a" * 700)
    await session.append_audio_chunk(b"b" * 700)
    await session.finish_audio_stream()

    await ws._process_audio_and_respond(session)

    transcriptions = _json_messages(fake_websocket, ws.MSG_TRANSCRIPTION)
    assert transcriptions[0]["text"] == "partial transcript"
    assert transcriptions[0]["final"] is False
    assert transcriptions[0]["streaming"] is True
    assert transcriptions[-1]["text"] == "I need support today."
    assert transcriptions[-1]["final"] is True
    assert stt.transcribe_called is False

    audio_end = _json_messages(fake_websocket, ws.MSG_AUDIO_END)[0]
    assert audio_end["timings"]["stt_provider"] == "streaming_stt"
    assert audio_end["timings"]["stt_streaming"] is True
    assert audio_end["timings"]["stt_batch_fallback"] is False
    assert audio_end["timings"]["audio_bytes"] == 1400
    assert audio_end["timings"]["tts_phrase_count"] == 1
    assert fake_websocket.sent_bytes == [b"audio:Rose response"]


@pytest.mark.asyncio
async def test_websocket_streaming_stt_empty_final_falls_back_to_batch(monkeypatch):
    stt = EmptyStreamingSTT()
    recorded_counters = []
    monkeypatch.setattr(ws, "get_stt", lambda: stt)
    monkeypatch.setattr(ws, "get_tts", lambda: FakeTTS())
    monkeypatch.setattr(
        ws.metrics,
        "increment_counter",
        lambda name, value=1, tags=None: recorded_counters.append((name, value, tags)),
    )

    fake_websocket = FakeWebSocket(FakeGraph())
    session = ws.VoiceWebSocketSession(fake_websocket, "session-streaming-empty")

    session.start_listening_turn()
    await session.append_audio_chunk(b"a" * 700)
    await session.append_audio_chunk(b"b" * 700)
    await session.finish_audio_stream()

    await ws._process_audio_and_respond(session)

    assert stt.transcribe_called is True
    transcriptions = _json_messages(fake_websocket, ws.MSG_TRANSCRIPTION)
    assert transcriptions == [
        {
            "type": ws.MSG_TRANSCRIPTION,
            "text": "I need support today.",
            "final": True,
            "provider": "streaming_stt",
            "streaming": True,
        }
    ]
    assert fake_websocket.sent_bytes == [b"audio:Rose response"]
    assert _json_messages(fake_websocket, ws.MSG_AUDIO_END)[0]["timings"]["stt_batch_fallback"] is True
    assert recorded_counters == [("ws_voice_stt_batch_fallback_total", 1, {"stt_provider": "streaming_stt"})]


@pytest.mark.asyncio
async def test_websocket_streaming_stt_error_logs_redacted_and_falls_back_to_batch(monkeypatch):
    fake_logger = FakeLogger()
    stt = SensitiveFailingStreamingSTT()

    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr(ws, "logger", fake_logger)
    monkeypatch.setattr(ws, "get_stt", lambda: stt)
    monkeypatch.setattr(ws, "get_tts", lambda: FakeTTS())

    fake_websocket = FakeWebSocket(FakeGraph())
    session = ws.VoiceWebSocketSession(fake_websocket, "session-streaming-error")

    session.start_listening_turn()
    await session.append_audio_chunk(b"a" * 1200)
    await session.finish_audio_stream()

    await ws._process_audio_and_respond(session)

    fallback_logs = [
        kwargs for event, kwargs in fake_logger.warning_calls if event == "ws_streaming_stt_failed_batch_fallback"
    ]
    assert fallback_logs
    assert fallback_logs[0]["error"] == REDACTED_TEXT
    assert fallback_logs[0]["session_log_id"] == session_id_for_log("session-streaming-error")
    assert fallback_logs[0]["exc_info"] is False
    assert "session-streaming-error" not in str(fake_logger.warning_calls)
    assert "private grief" not in str(fake_logger.warning_calls)
    assert stt.transcribe_called is True
    assert _json_messages(fake_websocket, ws.MSG_TRANSCRIPTION)[-1]["text"] == "I need support today."
    assert fake_websocket.sent_bytes == [b"audio:Rose response"]
    assert _json_messages(fake_websocket, ws.MSG_AUDIO_END)[0]["timings"]["stt_batch_fallback"] is True


@pytest.mark.asyncio
async def test_websocket_batch_stt_keeps_buffered_turn_behavior(monkeypatch):
    stt = BatchSTT()
    monkeypatch.setattr(ws, "get_stt", lambda: stt)
    monkeypatch.setattr(ws, "get_tts", lambda: FakeTTS())

    fake_websocket = FakeWebSocket(FakeGraph())
    session = ws.VoiceWebSocketSession(fake_websocket, "session-2")

    session.start_listening_turn()
    await session.append_audio_chunk(b"x" * 1200)
    await session.finish_audio_stream()

    await ws._process_audio_and_respond(session)

    assert stt.transcribed_audio == b"x" * 1200
    assert fake_websocket.app.state.compiled_graph.configs[0]["configurable"]["skip_tts"] is True
    transcriptions = _json_messages(fake_websocket, ws.MSG_TRANSCRIPTION)
    assert len(transcriptions) == 1
    assert transcriptions[0]["text"] == "I need support today."
    assert transcriptions[0]["final"] is True
    assert transcriptions[0]["streaming"] is False

    audio_end = _json_messages(fake_websocket, ws.MSG_AUDIO_END)[0]
    assert audio_end["timings"]["stt_provider"] == "groq_stt"
    assert audio_end["timings"]["stt_streaming"] is False
    assert audio_end["timings"]["stt_batch_fallback"] is False
    assert audio_end["timings"]["audio_bytes"] == 1200
    assert audio_end["timings"]["tts_phrase_count"] == 1


@pytest.mark.asyncio
async def test_websocket_short_audio_prompts_retry_without_calling_stt(monkeypatch):
    stt = BatchSTT()
    tts = FakeTTS()
    monkeypatch.setattr(ws, "get_stt", lambda: stt)
    monkeypatch.setattr(ws, "get_tts", lambda: tts)

    fake_websocket = FakeWebSocket(FakeGraph())
    session = ws.VoiceWebSocketSession(fake_websocket, "session-3")

    session.start_listening_turn()
    await session.append_audio_chunk(b"too-short")
    await session.finish_audio_stream()

    await ws._process_audio_and_respond(session)

    assert stt.transcribed_audio is None
    assert _json_messages(fake_websocket, ws.MSG_TURN_INCOMPLETE) == [
        {"type": ws.MSG_TURN_INCOMPLETE, "reason": "audio_too_short"}
    ]
    assert _json_messages(fake_websocket, ws.MSG_RESPONSE)[0]["text"] == ws.NO_SPEECH_PROMPT
    assert tts.texts == [ws.NO_SPEECH_PROMPT]
    assert fake_websocket.sent_bytes == [f"audio:{ws.NO_SPEECH_PROMPT}".encode()]
    audio_end = _json_messages(fake_websocket, ws.MSG_AUDIO_END)[0]
    assert audio_end["interrupted"] is False
    assert audio_end["timings"]["audio_bytes"] == len(b"too-short")
    assert audio_end["timings"]["tts_phrase_count"] == 1


@pytest.mark.asyncio
async def test_websocket_empty_transcription_prompts_retry_and_closes_turn(monkeypatch):
    stt = BatchSTT(transcript="")
    tts = FakeTTS()
    monkeypatch.setattr(ws, "get_stt", lambda: stt)
    monkeypatch.setattr(ws, "get_tts", lambda: tts)

    fake_websocket = FakeWebSocket(FakeGraph())
    session = ws.VoiceWebSocketSession(fake_websocket, "session-empty-transcription")

    session.start_listening_turn()
    await session.append_audio_chunk(b"x" * 1200)
    await session.finish_audio_stream()

    await ws._process_audio_and_respond(session)

    assert stt.transcribed_audio == b"x" * 1200
    assert fake_websocket.app.state.compiled_graph.payloads == []
    assert _json_messages(fake_websocket, ws.MSG_TURN_INCOMPLETE) == [
        {"type": ws.MSG_TURN_INCOMPLETE, "reason": "empty_transcription"}
    ]
    assert _json_messages(fake_websocket, ws.MSG_RESPONSE)[0]["text"] == ws.NO_SPEECH_PROMPT
    assert tts.texts == [ws.NO_SPEECH_PROMPT]
    assert _json_messages(fake_websocket, ws.MSG_AUDIO_END)[0]["timings"]["tts_phrase_count"] == 1


def test_split_text_for_tts_prefers_sentence_boundaries():
    text = "Breathe with me for a second. Let your shoulders drop. We can take this one small step at a time."

    assert ws.split_text_for_tts(text) == [
        "Breathe with me for a second. Let your shoulders drop.",
        "We can take this one small step at a time.",
    ]


def test_split_text_for_tts_splits_long_sentences_on_words():
    text = " ".join(["grounding"] * 40)

    chunks = ws.split_text_for_tts(text, max_chars=80)

    assert len(chunks) > 1
    assert all(len(chunk) <= 80 for chunk in chunks)


@pytest.mark.asyncio
async def test_websocket_streams_tts_phrase_by_phrase(monkeypatch):
    stt = BatchSTT()
    tts = FakeTTS()
    monkeypatch.setattr(ws, "get_stt", lambda: stt)
    monkeypatch.setattr(ws, "get_tts", lambda: tts)

    response = "Breathe with me for a second. Let your shoulders drop. We can take this one small step at a time."
    fake_websocket = FakeWebSocket(FakeGraph(response))
    session = ws.VoiceWebSocketSession(fake_websocket, "session-4")

    session.start_listening_turn()
    await session.append_audio_chunk(b"x" * 1200)
    await session.finish_audio_stream()

    await ws._process_audio_and_respond(session)

    assert tts.texts == [
        "Breathe with me for a second. Let your shoulders drop.",
        "We can take this one small step at a time.",
    ]
    assert fake_websocket.sent_bytes == [
        b"audio:Breathe with me for a second. Let your shoulders drop.",
        b"audio:We can take this one small step at a time.",
    ]

    audio_start = _json_messages(fake_websocket, ws.MSG_AUDIO_START)[0]
    assert audio_start["phrase_count"] == 2

    audio_end = _json_messages(fake_websocket, ws.MSG_AUDIO_END)[0]
    assert audio_end["timings"]["tts_phrase_count"] == 2
    assert audio_end["timings"]["tts_ms"] is not None
    assert audio_end["timings"]["mic_to_first_audio_ms"] is not None


@pytest.mark.asyncio
async def test_websocket_tts_phrase_streaming_respects_interrupt(monkeypatch):
    stt = BatchSTT()
    monkeypatch.setattr(ws, "get_stt", lambda: stt)

    response = "First sentence is spoken. Second sentence should not play after interruption."
    fake_websocket = FakeWebSocket(FakeGraph(response))
    session = ws.VoiceWebSocketSession(fake_websocket, "session-5")
    tts = FakeTTS(interrupt_session=session)
    monkeypatch.setattr(ws, "get_tts", lambda: tts)
    session.tts = tts

    session.start_listening_turn()
    await session.append_audio_chunk(b"x" * 1200)
    await session.finish_audio_stream()

    await ws._process_audio_and_respond(session)

    assert tts.texts == ["First sentence is spoken."]
    assert fake_websocket.sent_bytes == [b"audio:First sentence is spoken."]

    audio_end = _json_messages(fake_websocket, ws.MSG_AUDIO_END)[0]
    assert audio_end["interrupted"] is True


@pytest.mark.asyncio
async def test_websocket_tts_failure_degrades_to_text_only_turn(monkeypatch):
    stt = BatchSTT()
    tts = FailingTTS()
    monkeypatch.setattr(ws, "get_stt", lambda: stt)
    monkeypatch.setattr(ws, "get_tts", lambda: tts)

    fake_websocket = FakeWebSocket(FakeGraph("I am here with you."))
    session = ws.VoiceWebSocketSession(fake_websocket, "session-tts-fallback")

    session.start_listening_turn()
    await session.append_audio_chunk(b"x" * 1200)
    await session.finish_audio_stream()

    await ws._process_audio_and_respond(session)

    assert fake_websocket.sent_bytes == []
    assert _json_messages(fake_websocket, ws.MSG_RESPONSE)[0]["text"] == "I am here with you."
    assert _json_messages(fake_websocket, ws.MSG_AUDIO_UNAVAILABLE)[0]["text"] == "I am here with you."
    assert _json_messages(fake_websocket, ws.MSG_AUDIO_END)[0]["interrupted"] is False
    assert _json_messages(fake_websocket, ws.MSG_ERROR) == []


@pytest.mark.asyncio
async def test_websocket_tts_failure_logs_redacted_provider_errors(monkeypatch):
    fake_logger = FakeLogger()
    stt = BatchSTT()
    tts = SensitiveFailingTTS()
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr(ws, "logger", fake_logger)
    monkeypatch.setattr(ws, "get_stt", lambda: stt)
    monkeypatch.setattr(ws, "get_tts", lambda: tts)

    fake_websocket = FakeWebSocket(FakeGraph("I am here with you."))
    session = ws.VoiceWebSocketSession(fake_websocket, "session-tts-privacy")

    session.start_listening_turn()
    await session.append_audio_chunk(b"x" * 1200)
    await session.finish_audio_stream()

    await ws._process_audio_and_respond(session)

    failure_logs = {event: kwargs for event, kwargs in fake_logger.warning_calls if event.startswith("ws_tts_")}
    assert failure_logs["ws_tts_streaming_failed"]["error"] == REDACTED_TEXT
    assert failure_logs["ws_tts_streaming_failed"]["session_log_id"] == session_id_for_log("session-tts-privacy")
    assert failure_logs["ws_tts_streaming_failed"]["exc_info"] is False
    assert failure_logs["ws_tts_fallback_failed_text_only"]["error"] == REDACTED_TEXT
    assert failure_logs["ws_tts_fallback_failed_text_only"]["session_log_id"] == session_id_for_log(
        "session-tts-privacy"
    )
    assert failure_logs["ws_tts_fallback_failed_text_only"]["exc_info"] is False
    assert "session-tts-privacy" not in str(fake_logger.warning_calls)
    assert "private grief" not in str(fake_logger.warning_calls)
    assert _json_messages(fake_websocket, ws.MSG_AUDIO_UNAVAILABLE)[0]["text"] == "I am here with you."


@pytest.mark.asyncio
async def test_websocket_incomplete_turn_prompts_for_continuation_without_graph(monkeypatch):
    stt = BatchSTT(transcript="I feel like")
    tts = FakeTTS()
    graph = FakeGraph("should not be used")
    recorded_counters = []

    monkeypatch.setattr(ws, "get_stt", lambda: stt)
    monkeypatch.setattr(ws, "get_tts", lambda: tts)
    monkeypatch.setattr(
        ws.metrics,
        "increment_counter",
        lambda name, value=1, tags=None: recorded_counters.append((name, value, tags)),
    )

    fake_websocket = FakeWebSocket(graph)
    session = ws.VoiceWebSocketSession(fake_websocket, "session-incomplete")

    session.start_listening_turn()
    await session.append_audio_chunk(b"x" * 1200)
    await session.finish_audio_stream()

    await ws._process_audio_and_respond(session)

    assert graph.payloads == []
    assert _json_messages(fake_websocket, ws.MSG_TURN_INCOMPLETE) == [
        {"type": ws.MSG_TURN_INCOMPLETE, "reason": "dangling_phrase"}
    ]
    assert _json_messages(fake_websocket, ws.MSG_RESPONSE)[0]["text"] == ws.CONTINUATION_PROMPT
    assert tts.texts == [ws.CONTINUATION_PROMPT]
    assert recorded_counters == [
        (
            "ws_voice_turn_incomplete_total",
            1,
            {"stt_provider": "groq_stt", "reason": "dangling_phrase"},
        )
    ]
    assert _json_messages(fake_websocket, ws.MSG_AUDIO_END)[0]["timings"]["tts_phrase_count"] == 1


@pytest.mark.asyncio
async def test_websocket_streams_llm_deltas_into_phrase_tts(monkeypatch):
    stt = BatchSTT()
    tts = FakeTTS()
    monkeypatch.setattr(ws, "get_stt", lambda: stt)
    monkeypatch.setattr(ws, "get_tts", lambda: tts)

    graph = StreamingFakeGraph(["Breathe with me. ", "Let your shoulders drop."])
    fake_websocket = FakeWebSocket(graph)
    session = ws.VoiceWebSocketSession(fake_websocket, "session-6")

    session.start_listening_turn()
    await session.append_audio_chunk(b"x" * 1200)
    await session.finish_audio_stream()

    await ws._process_audio_and_respond(session)

    assert graph.ainvoke_called is False
    assert graph.configs[0]["configurable"]["skip_tts"] is True
    assert _json_messages(fake_websocket, ws.MSG_RESPONSE_DELTA) == [
        {"type": ws.MSG_RESPONSE_DELTA, "text": "Breathe with me. "},
        {"type": ws.MSG_RESPONSE_DELTA, "text": "Let your shoulders drop."},
    ]
    assert tts.texts == ["Breathe with me.", "Let your shoulders drop."]
    assert fake_websocket.sent_bytes == [
        b"audio:Breathe with me.",
        b"audio:Let your shoulders drop.",
    ]

    response = _json_messages(fake_websocket, ws.MSG_RESPONSE)[0]
    assert response["text"] == "Breathe with me. Let your shoulders drop."

    audio_end = _json_messages(fake_websocket, ws.MSG_AUDIO_END)[0]
    assert audio_end["timings"]["tts_phrase_count"] == 2


@pytest.mark.asyncio
async def test_websocket_streaming_sanitizes_markdown_chunks(monkeypatch):
    stt = BatchSTT()
    tts = FakeTTS()
    monkeypatch.setattr(ws, "get_stt", lambda: stt)
    monkeypatch.setattr(ws, "get_tts", lambda: tts)

    graph = StreamingFakeGraph(["## Grounding\n- *softly* Breathe with me."])
    fake_websocket = FakeWebSocket(graph)
    session = ws.VoiceWebSocketSession(fake_websocket, "session-6-clean")

    session.start_listening_turn()
    await session.append_audio_chunk(b"x" * 1200)
    await session.finish_audio_stream()

    await ws._process_audio_and_respond(session)

    assert tts.texts == ["Breathe with me."]
    response = _json_messages(fake_websocket, ws.MSG_RESPONSE)[0]
    assert response["text"] == "Breathe with me."


@pytest.mark.asyncio
async def test_websocket_records_streaming_response_quality_issues(monkeypatch):
    stt = BatchSTT()
    tts = FakeTTS()
    recorded_counters = []

    monkeypatch.setattr(ws, "get_stt", lambda: stt)
    monkeypatch.setattr(ws, "get_tts", lambda: tts)
    monkeypatch.setattr(
        ws.metrics,
        "increment_counter",
        lambda name, value=1, tags=None: recorded_counters.append((name, value, tags)),
    )

    graph = StreamingFakeGraph(["You need me more than anyone. Talk to me for hours."])
    fake_websocket = FakeWebSocket(graph)
    session = ws.VoiceWebSocketSession(fake_websocket, "session-quality")

    session.start_listening_turn()
    await session.append_audio_chunk(b"x" * 1200)
    await session.finish_audio_stream()

    await ws._process_audio_and_respond(session)

    assert _json_messages(fake_websocket, ws.MSG_RESPONSE)[0]["text"] == (
        "You need me more than anyone. Talk to me for hours."
    )
    assert (
        "voice_response_quality_issues_total",
        1,
        {"issue_code": "dependency_language"},
    ) in recorded_counters


@pytest.mark.asyncio
async def test_websocket_falls_back_to_graph_invoke_when_stream_has_no_text(monkeypatch):
    stt = BatchSTT()
    tts = FakeTTS()
    monkeypatch.setattr(ws, "get_stt", lambda: stt)
    monkeypatch.setattr(ws, "get_tts", lambda: tts)

    graph = EmptyStreamingFakeGraph("Fallback response.")
    fake_websocket = FakeWebSocket(graph)
    session = ws.VoiceWebSocketSession(fake_websocket, "session-7")

    session.start_listening_turn()
    await session.append_audio_chunk(b"x" * 1200)
    await session.finish_audio_stream()

    await ws._process_audio_and_respond(session)

    assert graph.configs[0]["configurable"]["skip_tts"] is True
    assert graph.configs[1]["configurable"]["skip_tts"] is True
    assert tts.texts == ["Fallback response."]


@pytest.mark.asyncio
async def test_websocket_llm_stream_failure_logs_redacted_error_and_falls_back(monkeypatch):
    fake_logger = FakeLogger()
    stt = BatchSTT()
    tts = FakeTTS()
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr(ws, "logger", fake_logger)
    monkeypatch.setattr(ws, "get_stt", lambda: stt)
    monkeypatch.setattr(ws, "get_tts", lambda: tts)

    graph = SensitiveFailingStreamingGraph("Fallback response.")
    fake_websocket = FakeWebSocket(graph)
    session = ws.VoiceWebSocketSession(fake_websocket, "session-llm-privacy")

    session.start_listening_turn()
    await session.append_audio_chunk(b"x" * 1200)
    await session.finish_audio_stream()

    await ws._process_audio_and_respond(session)

    stream_logs = [kwargs for event, kwargs in fake_logger.warning_calls if event == "ws_llm_stream_failed"]
    assert stream_logs
    assert stream_logs[0]["error"] == REDACTED_TEXT
    assert stream_logs[0]["session_log_id"] == session_id_for_log("session-llm-privacy")
    assert stream_logs[0]["exc_info"] is False
    assert "session-llm-privacy" not in str(fake_logger.warning_calls)
    assert "private grief" not in str(fake_logger.warning_calls)
    assert _json_messages(fake_websocket, ws.MSG_RESPONSE)[0]["text"] == "Fallback response."


@pytest.mark.asyncio
async def test_websocket_processing_error_logs_redacted_provider_error(monkeypatch):
    fake_logger = FakeLogger()
    stt = SensitiveFailingSTT()
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr(ws, "logger", fake_logger)
    monkeypatch.setattr(ws, "get_stt", lambda: stt)
    monkeypatch.setattr(ws, "get_tts", lambda: FakeTTS())

    fake_websocket = FakeWebSocket(FakeGraph())
    session = ws.VoiceWebSocketSession(fake_websocket, "session-processing-privacy")

    session.start_listening_turn()
    await session.append_audio_chunk(b"x" * 1200)
    await session.finish_audio_stream()

    await ws._process_audio_and_respond(session)

    error_logs = [kwargs for event, kwargs in fake_logger.error_calls if event == "ws_processing_error"]
    assert error_logs
    assert error_logs[0]["error"] == REDACTED_TEXT
    assert error_logs[0]["session_log_id"] == session_id_for_log("session-processing-privacy")
    assert error_logs[0]["exc_info"] is False
    assert "session-processing-privacy" not in str(fake_logger.error_calls)
    assert "private grief" not in str(fake_logger.error_calls)
    assert _json_messages(fake_websocket, ws.MSG_ERROR) == [{"type": ws.MSG_ERROR, "message": "Processing failed"}]


def test_record_websocket_turn_metrics_records_latency_histograms(monkeypatch):
    recorded = []

    def record_histogram(name, value, tags=None):
        recorded.append((name, value, tags))

    monkeypatch.setattr(ws.metrics, "record_histogram", record_histogram)

    ws._record_websocket_turn_metrics(
        {
            "stt_provider": "streaming_stt",
            "stt_streaming": True,
            "stt_batch_fallback": False,
            "audio_bytes": 2048,
            "stt_ms": 40.2,
            "workflow_ms": 85.5,
            "tts_ms": 120.1,
            "mic_to_first_audio_ms": 250.0,
            "turn_total_ms": 410.7,
            "tts_phrase_count": 2,
        }
    )

    assert recorded == [
        (
            "ws_voice_audio_bytes",
            2048,
            {"stt_provider": "streaming_stt", "stt_streaming": True, "stt_batch_fallback": False},
        ),
        (
            "ws_voice_stt_ms",
            40.2,
            {"stt_provider": "streaming_stt", "stt_streaming": True, "stt_batch_fallback": False},
        ),
        (
            "ws_voice_workflow_ms",
            85.5,
            {"stt_provider": "streaming_stt", "stt_streaming": True, "stt_batch_fallback": False},
        ),
        (
            "ws_voice_tts_ms",
            120.1,
            {"stt_provider": "streaming_stt", "stt_streaming": True, "stt_batch_fallback": False},
        ),
        (
            "ws_voice_mic_to_first_audio_ms",
            250.0,
            {"stt_provider": "streaming_stt", "stt_streaming": True, "stt_batch_fallback": False},
        ),
        (
            "ws_voice_turn_total_ms",
            410.7,
            {"stt_provider": "streaming_stt", "stt_streaming": True, "stt_batch_fallback": False},
        ),
        (
            "ws_voice_tts_phrase_count",
            2,
            {"stt_provider": "streaming_stt", "stt_streaming": True, "stt_batch_fallback": False},
        ),
    ]
