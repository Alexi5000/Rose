"""WebSocket endpoint for real-time voice streaming.

file: src/ai_companion/interfaces/web/routes/voice_websocket.py
description: Phase 6 - Bi-directional WebSocket for low-latency voice interactions
reference: src/ai_companion/interfaces/web/routes/voice.py, docs/BASELINE_METRICS.md

This module provides WebSocket-based voice processing that enables:
- Real-time audio streaming from client to server
- Overlapped processing (STT while receiving, TTS while generating)
- Streaming responses back to client
- Barge-in support (client can interrupt Rose)

Protocol:
1. Client connects to /api/v1/voice/ws?session_id=<uuid>
2. Client sends binary audio chunks
3. Server sends JSON control messages and binary audio responses
4. Client can send interrupt signal to stop Rose mid-response

Message Types (JSON):
- {"type": "start_listening"}: Begin audio capture
- {"type": "stop_listening"}: End audio capture, process
- {"type": "interrupt"}: Stop current response
- {"type": "transcription", "text": "..."}: Partial/final transcription
- {"type": "response", "text": "..."}: Rose's response text
- {"type": "audio_start"}: Audio streaming starting
- {"type": "audio_end"}: Audio streaming complete
- {"type": "error", "message": "..."}: Error occurred

Binary Messages:
- Client -> Server: Audio chunks (webm/opus)
- Server -> Client: Audio chunks (mp3)
"""

import asyncio
import json
import re
import time
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage

from ai_companion.core.logging_config import get_logger
from ai_companion.core.metrics import metrics
from ai_companion.core.privacy_logging import exc_info_for_log, exception_message_for_log, session_id_for_log
from ai_companion.interfaces.web.routes.voice import get_stt, get_tts
from ai_companion.modules.response_quality import analyze_voice_response, sanitize_voice_response
from ai_companion.modules.speech.turn_detection import CONTINUATION_PROMPT, assess_turn_completion
from ai_companion.settings import settings

logger = get_logger(__name__)

router = APIRouter()

# WebSocket message types
MSG_START_LISTENING = "start_listening"
MSG_STOP_LISTENING = "stop_listening"
MSG_INTERRUPT = "interrupt"
MSG_TRANSCRIPTION = "transcription"
MSG_RESPONSE = "response"
MSG_AUDIO_START = "audio_start"
MSG_AUDIO_END = "audio_end"
MSG_AUDIO_UNAVAILABLE = "audio_unavailable"
MSG_ERROR = "error"
MSG_CONNECTED = "connected"
MSG_RESPONSE_DELTA = "response_delta"
MSG_TURN_INCOMPLETE = "turn_incomplete"

MIN_AUDIO_BYTES = 1000
MS_PER_SECOND = 1000
STREAM_END = None
MAX_TTS_PHRASE_CHARS = 70
MIN_TTS_PHRASE_CHARS = 24
NO_SPEECH_PROMPT = "I didn't catch that. Try once more when you're ready."


class VoiceWebSocketSession:
    """Manages state for a single WebSocket voice session.

    Handles audio buffering, interruption signals, and response streaming.
    """

    def __init__(self, websocket: WebSocket, session_id: str):
        self.websocket = websocket
        self.session_id = session_id
        self.session_log_id = session_id_for_log(session_id)
        self.audio_buffer: bytearray = bytearray()
        self.audio_queue: asyncio.Queue[bytes | None] | None = None
        self.transcription_task: asyncio.Task[str] | None = None
        self.processing_task: asyncio.Task[None] | None = None
        self.turn_started_at: float | None = None
        self.first_audio_at: float | None = None
        self.stt_started_at: float | None = None
        self.stt_completed_at: float | None = None
        self.stt_batch_fallback = False
        self.workflow_completed_at: float | None = None
        self.tts_started_at: float | None = None
        self.tts_completed_at: float | None = None
        self.tts_phrase_count = 0
        self.is_listening = False
        self.is_responding = False
        self.interrupted = False
        self.audio_end_sent = False
        self.stt = get_stt()
        self.tts = get_tts()

    async def send_json(self, msg_type: str, **kwargs) -> None:
        """Send a JSON control message to the client."""
        message = {"type": msg_type, **kwargs}
        await self.websocket.send_json(message)

    async def send_audio(self, audio_chunk: bytes) -> None:
        """Send audio data to the client."""
        if self.first_audio_at is None:
            self.first_audio_at = time.perf_counter()
        await self.websocket.send_bytes(audio_chunk)

    def handle_interrupt(self) -> None:
        """Handle interruption signal from client."""
        self.interrupted = True
        if self.transcription_task and not self.transcription_task.done():
            self.transcription_task.cancel()
        current_task = asyncio.current_task()
        if self.processing_task and not self.processing_task.done() and self.processing_task is not current_task:
            self.processing_task.cancel()
        logger.info("ws_session_interrupted", session_log_id=self.session_log_id)

    def reset_for_new_turn(self) -> None:
        """Reset session state for a new conversation turn."""
        if self.transcription_task and not self.transcription_task.done():
            self.transcription_task.cancel()
        if self.processing_task and not self.processing_task.done():
            self.processing_task.cancel()
        self.audio_buffer.clear()
        self.audio_queue = None
        self.transcription_task = None
        self.processing_task = None
        self.turn_started_at = None
        self.first_audio_at = None
        self.stt_started_at = None
        self.stt_completed_at = None
        self.stt_batch_fallback = False
        self.workflow_completed_at = None
        self.tts_started_at = None
        self.tts_completed_at = None
        self.tts_phrase_count = 0
        self.is_listening = False
        self.is_responding = False
        self.interrupted = False
        self.audio_end_sent = False

    def start_listening_turn(self) -> None:
        """Start a new listening turn and arm streaming STT when available."""
        self.reset_for_new_turn()
        self.turn_started_at = time.perf_counter()
        self.is_listening = True

        if self.stt.supports_streaming:
            self.audio_queue = asyncio.Queue()
            self.transcription_task = asyncio.create_task(
                _consume_streaming_transcription(self),
                name=f"ws_streaming_stt_{self.session_id}",
            )

    async def append_audio_chunk(self, audio_chunk: bytes) -> None:
        """Append audio to the current turn and forward it to streaming STT."""
        if not audio_chunk:
            return
        self.audio_buffer.extend(audio_chunk)
        if self.audio_queue is not None:
            await self.audio_queue.put(audio_chunk)

    async def finish_audio_stream(self) -> None:
        """Signal that no more audio chunks will arrive for this turn."""
        self.is_listening = False
        if self.audio_queue is not None:
            await self.audio_queue.put(STREAM_END)

    def timing_payload(self) -> dict[str, Any]:
        """Return latency metadata for this turn."""
        now = time.perf_counter()
        turn_start = self.turn_started_at or now
        return {
            "stt_provider": self.stt.name,
            "stt_streaming": self.stt.supports_streaming,
            "stt_batch_fallback": self.stt_batch_fallback,
            "audio_bytes": len(self.audio_buffer),
            "stt_ms": _elapsed_ms(self.stt_started_at, self.stt_completed_at),
            "workflow_ms": _elapsed_ms(self.stt_completed_at, self.workflow_completed_at),
            "tts_ms": _elapsed_ms(self.tts_started_at, self.tts_completed_at),
            "tts_phrase_count": self.tts_phrase_count,
            "mic_to_first_audio_ms": _elapsed_ms(turn_start, self.first_audio_at),
            "turn_total_ms": round((now - turn_start) * MS_PER_SECOND, 2),
        }


def _elapsed_ms(start: float | None, end: float | None) -> float | None:
    if start is None or end is None:
        return None
    return round((end - start) * MS_PER_SECOND, 2)


def _record_websocket_turn_metrics(timings: dict[str, Any]) -> None:
    """Record WebSocket voice turn latency histograms."""
    metric_names = {
        "audio_bytes": "ws_voice_audio_bytes",
        "stt_ms": "ws_voice_stt_ms",
        "workflow_ms": "ws_voice_workflow_ms",
        "tts_ms": "ws_voice_tts_ms",
        "mic_to_first_audio_ms": "ws_voice_mic_to_first_audio_ms",
        "turn_total_ms": "ws_voice_turn_total_ms",
        "tts_phrase_count": "ws_voice_tts_phrase_count",
    }
    tags = {
        "stt_provider": timings["stt_provider"],
        "stt_streaming": timings["stt_streaming"],
        "stt_batch_fallback": timings.get("stt_batch_fallback", False),
    }

    for timing_key, metric_name in metric_names.items():
        value = timings.get(timing_key)
        if value is not None:
            metrics.record_histogram(metric_name, value, tags=tags)


def _record_websocket_response_quality(response_text: str, session_id: str) -> None:
    """Record deterministic response-quality issues without raw response text."""

    issues = analyze_voice_response(response_text)
    if not issues:
        return

    issue_codes = [issue.code for issue in issues]
    for issue_code in issue_codes:
        metrics.increment_counter("voice_response_quality_issues_total", tags={"issue_code": issue_code})

    logger.warning(
        "ws_voice_response_quality_issues",
        session_log_id=session_id_for_log(session_id),
        issue_codes=issue_codes,
        issue_count=len(issue_codes),
        response_words=len(response_text.split()),
    )


async def _audio_stream_from_queue(queue: asyncio.Queue[bytes | None]):
    while True:
        chunk = await queue.get()
        if chunk is STREAM_END:
            break
        yield chunk


async def _consume_streaming_transcription(session: VoiceWebSocketSession) -> str:
    """Consume streaming STT results and send partial transcripts to the client."""
    if session.audio_queue is None:
        return ""

    final_transcript = ""
    session.stt_started_at = time.perf_counter()
    async for transcript in session.stt.transcribe_streaming(_audio_stream_from_queue(session.audio_queue)):
        if not transcript:
            continue
        final_transcript = transcript
        await session.send_json(
            MSG_TRANSCRIPTION,
            text=transcript,
            final=False,
            provider=session.stt.name,
            streaming=True,
        )

    session.stt_completed_at = time.perf_counter()
    return final_transcript


async def _transcribe_audio_for_turn(session: VoiceWebSocketSession, audio_data: bytes) -> str:
    """Return a final transcript, falling back to buffered STT when streaming is unavailable or weak."""

    session.stt_started_at = session.stt_started_at or time.perf_counter()
    if session.transcription_task:
        try:
            transcription = await session.transcription_task
        except Exception as streaming_error:
            logger.warning(
                "ws_streaming_stt_failed_batch_fallback",
                session_log_id=session.session_log_id,
                stt_provider=session.stt.name,
                error=exception_message_for_log(streaming_error),
                exc_info=exc_info_for_log(),
            )
            transcription = ""

        if transcription and transcription.strip():
            return transcription

        logger.info(
            "ws_streaming_stt_empty_batch_fallback",
            session_log_id=session.session_log_id,
            stt_provider=session.stt.name,
        )

    if session.transcription_task:
        session.stt_batch_fallback = True
        metrics.increment_counter(
            "ws_voice_stt_batch_fallback_total",
            tags={"stt_provider": session.stt.name},
        )

    transcription = await session.stt.transcribe(audio_data)
    session.stt_completed_at = time.perf_counter()
    return transcription


def split_text_for_tts(text: str, max_chars: int = MAX_TTS_PHRASE_CHARS) -> list[str]:
    """Split response text into voice-friendly chunks for faster TTS start."""
    normalized = " ".join(text.split())
    if not normalized:
        return []

    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if part.strip()]
    phrases: list[str] = []
    current = ""

    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence
        if current and len(candidate) > max_chars and len(current) >= MIN_TTS_PHRASE_CHARS:
            phrases.append(current)
            current = sentence
        elif len(sentence) > max_chars:
            if current:
                phrases.append(current)
                current = ""
            phrases.extend(_split_long_phrase(sentence, max_chars))
        else:
            current = candidate

    if current:
        phrases.append(current)

    return phrases


def _split_long_phrase(text: str, max_chars: int) -> list[str]:
    """Split a long sentence on comma/semicolon boundaries before words."""
    chunks: list[str] = []
    current = ""
    for segment in re.split(r"(?<=[,;:])\s+", text):
        segment = segment.strip()
        if not segment:
            continue
        candidate = f"{current} {segment}".strip() if current else segment
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = segment
        elif len(segment) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_on_words(segment, max_chars))
        else:
            current = candidate

    if current:
        chunks.append(current)
    return chunks


def _split_on_words(text: str, max_chars: int) -> list[str]:
    chunks: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip() if current else word
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = word
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


async def _stream_tts_response(session: VoiceWebSocketSession, response_text: str) -> None:
    """Stream response audio phrase-by-phrase for lower time-to-first-audio."""
    phrases = split_text_for_tts(response_text)
    if not phrases:
        return

    await _stream_tts_phrases(session, phrases, phrase_count=len(phrases))


async def _send_turn_continuation_prompt(
    session: VoiceWebSocketSession,
    reason: str,
    prompt: str = CONTINUATION_PROMPT,
) -> None:
    """Ask for a continuation when STT yields a clear dangling fragment."""

    metrics.increment_counter(
        "ws_voice_turn_incomplete_total",
        tags={"stt_provider": session.stt.name, "reason": reason},
    )
    logger.info(
        "ws_turn_incomplete",
        session_log_id=session.session_log_id,
        stt_provider=session.stt.name,
        reason=reason,
    )
    await session.send_json(MSG_TURN_INCOMPLETE, reason=reason)
    await session.send_json(MSG_RESPONSE, text=prompt)
    await _stream_tts_response(session, prompt)
    await _send_audio_end(session)


async def _send_audio_end(session: VoiceWebSocketSession, interrupted: bool | None = None) -> None:
    """Send the final audio_end control message once for the current turn."""

    if session.audio_end_sent:
        return

    timings = session.timing_payload()
    _record_websocket_turn_metrics(timings)
    await session.send_json(
        MSG_AUDIO_END,
        interrupted=session.interrupted if interrupted is None else interrupted,
        timings=timings,
    )
    session.audio_end_sent = True


async def _stream_tts_phrases(
    session: VoiceWebSocketSession,
    phrases: list[str],
    phrase_count: int | None = None,
) -> None:
    """Stream already-split TTS phrases."""
    phrases = [phrase for phrase in phrases if phrase]
    if not phrases:
        return

    fallback_text = " ".join(phrases)
    session.tts_phrase_count += len(phrases)
    if session.tts_started_at is None:
        session.tts_started_at = time.perf_counter()
    if session.tts_phrase_count == len(phrases):
        await session.send_json(MSG_AUDIO_START, phrase_count=phrase_count)

    try:
        for index, phrase in enumerate(phrases):
            if session.interrupted:
                logger.info(
                    "ws_interrupted_before_tts_phrase", session_log_id=session.session_log_id, phrase_index=index
                )
                break

            await session.send_json("audio_phrase_start", index=index, text=phrase)
            async for audio_chunk in session.tts.synthesize_streaming(phrase):
                if session.interrupted:
                    logger.info("ws_interrupted_during_tts", session_log_id=session.session_log_id, phrase_index=index)
                    break
                await session.send_audio(audio_chunk)
            await session.send_json("audio_phrase_end", index=index, interrupted=session.interrupted)

            if session.interrupted:
                break
    except Exception as tts_error:
        logger.warning(
            "ws_tts_streaming_failed",
            session_log_id=session.session_log_id,
            error=exception_message_for_log(tts_error),
            exc_info=exc_info_for_log(),
        )
        try:
            audio_bytes = await session.tts.synthesize(fallback_text)
            if not session.interrupted:
                await session.send_audio(audio_bytes)
        except Exception as fallback_error:
            logger.warning(
                "ws_tts_fallback_failed_text_only",
                session_log_id=session.session_log_id,
                error=exception_message_for_log(fallback_error),
                exc_info=exc_info_for_log(),
            )
            if not session.interrupted:
                await session.send_json(MSG_AUDIO_UNAVAILABLE, text=fallback_text)
    finally:
        session.tts_completed_at = time.perf_counter()


def pop_ready_tts_phrases(text: str, force: bool = False) -> tuple[list[str], str]:
    """Pop complete voice phrases from a streaming text buffer."""
    if not text.strip():
        return [], ""

    if force:
        return split_text_for_tts(text), ""

    boundary_end = 0
    for match in re.finditer(r"(?<=[.!?])\s+", text):
        boundary_end = match.end()

    stripped = text.strip()
    if not boundary_end and stripped.endswith((".", "!", "?")) and len(stripped) >= MIN_TTS_PHRASE_CHARS:
        boundary_end = len(text)

    if not boundary_end:
        return [], text

    ready_text = text[:boundary_end].strip()
    remainder = text[boundary_end:].strip()
    return split_text_for_tts(ready_text), remainder


def _event_text_delta(event: dict[str, Any]) -> str:
    """Extract text deltas from LangGraph/LangChain stream events."""
    if event.get("event") != "on_chat_model_stream":
        return ""
    metadata = event.get("metadata", {})
    graph_node = metadata.get("langgraph_node")
    if graph_node and graph_node != "audio_node":
        return ""

    chunk = event.get("data", {}).get("chunk")
    content = getattr(chunk, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)
    return ""


async def _stream_graph_response_to_tts(
    session: VoiceWebSocketSession,
    compiled_graph: Any,
    graph_input: dict[str, Any],
    config: dict[str, Any],
) -> str | None:
    """Stream LangGraph chat-model deltas into phrase TTS when supported."""
    if not hasattr(compiled_graph, "astream_events"):
        return None

    response_text = ""
    phrase_buffer = ""

    try:
        async with asyncio.timeout(settings.WORKFLOW_TIMEOUT_SECONDS):
            async for event in compiled_graph.astream_events(graph_input, config=config, version="v2"):
                if session.interrupted:
                    logger.info("ws_interrupted_during_llm_stream", session_log_id=session.session_log_id)
                    break

                delta = _event_text_delta(event)
                if not delta:
                    continue

                response_text += delta
                await session.send_json(MSG_RESPONSE_DELTA, text=delta)

                phrase_buffer += delta
                ready_phrases, phrase_buffer = pop_ready_tts_phrases(phrase_buffer)
                ready_phrases = [
                    phrase for phrase in (sanitize_voice_response(phrase) for phrase in ready_phrases) if phrase
                ]
                await _stream_tts_phrases(session, ready_phrases)

        session.workflow_completed_at = time.perf_counter()

        final_phrases, _ = pop_ready_tts_phrases(phrase_buffer, force=True)
        final_phrases = [phrase for phrase in (sanitize_voice_response(phrase) for phrase in final_phrases) if phrase]
        await _stream_tts_phrases(session, final_phrases)

        response_text = sanitize_voice_response(response_text)
        if response_text and session.tts_phrase_count == 0 and not session.interrupted:
            await _stream_tts_phrases(session, [response_text])
        if response_text:
            _record_websocket_response_quality(response_text, session.session_id)
            await session.send_json(MSG_RESPONSE, text=response_text)
            return response_text

    except Exception as stream_error:
        logger.warning(
            "ws_llm_stream_failed",
            session_log_id=session.session_log_id,
            error=exception_message_for_log(stream_error),
            exc_info=exc_info_for_log(),
        )
        if response_text:
            final_phrases, _ = pop_ready_tts_phrases(phrase_buffer, force=True)
            final_phrases = [
                phrase for phrase in (sanitize_voice_response(phrase) for phrase in final_phrases) if phrase
            ]
            await _stream_tts_phrases(session, final_phrases)
            response_text = sanitize_voice_response(response_text)
            if response_text and session.tts_phrase_count == 0 and not session.interrupted:
                await _stream_tts_phrases(session, [response_text])
            _record_websocket_response_quality(response_text, session.session_id)
            await session.send_json(MSG_RESPONSE, text=response_text)
            return response_text
        return None

    return None


@router.websocket("/voice/ws")
async def voice_websocket(
    websocket: WebSocket,
    session_id: str = Query(..., description="Session ID for conversation tracking"),
) -> None:
    """WebSocket endpoint for real-time voice streaming.

    Provides bi-directional audio streaming for low-latency voice interactions.
    Supports interruption (barge-in) while Rose is speaking.

    Args:
        websocket: FastAPI WebSocket connection
        session_id: Session identifier from /session/start
    """
    await websocket.accept()
    session_log_id = session_id_for_log(session_id)
    logger.info("ws_connection_accepted", session_log_id=session_log_id)

    session = VoiceWebSocketSession(websocket, session_id)

    # Send connection confirmation
    await session.send_json(MSG_CONNECTED, session_id=session_id)

    try:
        while True:
            # Receive message (text or binary)
            message = await websocket.receive()

            if message["type"] == "websocket.disconnect":
                break

            # Handle text messages (JSON control messages)
            if "text" in message:
                try:
                    data = json.loads(message["text"])
                    msg_type = data.get("type")

                    if msg_type == MSG_START_LISTENING:
                        if session.is_responding:
                            session.handle_interrupt()
                        session.start_listening_turn()
                        logger.debug(
                            "ws_start_listening",
                            session_log_id=session_log_id,
                            stt_provider=session.stt.name,
                            stt_streaming=session.stt.supports_streaming,
                        )

                    elif msg_type == MSG_STOP_LISTENING:
                        await session.finish_audio_stream()
                        logger.debug(
                            "ws_stop_listening",
                            session_log_id=session_log_id,
                            buffer_size=len(session.audio_buffer),
                        )

                        # Process the collected audio
                        if session.audio_buffer:
                            if session.processing_task and not session.processing_task.done():
                                session.handle_interrupt()
                                session.processing_task.cancel()
                            session.processing_task = asyncio.create_task(
                                _process_audio_and_respond(session),
                                name=f"ws_voice_process_{session_id_for_log(session_id)}",
                            )

                    elif msg_type == MSG_INTERRUPT:
                        session.handle_interrupt()
                        await _send_audio_end(session, interrupted=True)

                except json.JSONDecodeError as e:
                    logger.warning("ws_invalid_json", session_log_id=session_log_id, error=exception_message_for_log(e))
                    await session.send_json(MSG_ERROR, message="Invalid JSON message")

            # Handle binary messages (audio chunks)
            elif "bytes" in message:
                if session.is_listening:
                    await session.append_audio_chunk(message["bytes"])

    except WebSocketDisconnect:
        logger.info("ws_connection_closed", session_log_id=session_log_id)
        if session.processing_task and not session.processing_task.done():
            session.processing_task.cancel()

    except Exception as e:
        logger.error(
            "ws_error",
            session_log_id=session_log_id,
            error=exception_message_for_log(e),
            exc_info=exc_info_for_log(),
        )
        try:
            await session.send_json(MSG_ERROR, message="WebSocket voice session failed")
        except Exception:
            pass
        if session.processing_task and not session.processing_task.done():
            session.processing_task.cancel()


async def _process_audio_and_respond(session: VoiceWebSocketSession) -> None:
    """Process buffered audio and stream response back to client.

    This is the core processing pipeline for WebSocket voice:
    1. Transcribe audio (STT)
    2. Send transcription to client
    3. Run LangGraph workflow
    4. Send response text to client
    5. Stream TTS audio to client

    Supports interruption at any point.
    """
    session_id = session.session_id
    session_log_id = session.session_log_id

    try:
        # Step 1: Transcribe audio
        audio_data = bytes(session.audio_buffer)

        if len(audio_data) < MIN_AUDIO_BYTES:  # Too short to be meaningful
            logger.debug("ws_audio_too_short", session_log_id=session_log_id, size=len(audio_data))
            await _send_turn_continuation_prompt(session, "audio_too_short", prompt=NO_SPEECH_PROMPT)
            return

        transcription = await _transcribe_audio_for_turn(session, audio_data)

        if not transcription or not transcription.strip():
            logger.debug("ws_empty_transcription", session_log_id=session_log_id)
            await _send_turn_continuation_prompt(session, "empty_transcription", prompt=NO_SPEECH_PROMPT)
            return

        # Send transcription to client
        await session.send_json(
            MSG_TRANSCRIPTION,
            text=transcription,
            final=True,
            provider=session.stt.name,
            streaming=session.stt.supports_streaming,
        )

        if session.interrupted:
            return

        turn_completion = assess_turn_completion(transcription)
        if not turn_completion.is_complete:
            await _send_turn_continuation_prompt(session, turn_completion.reason)
            return

        # Step 2: Process through workflow
        session.is_responding = True

        # Use pre-compiled graph from app state (initialized in app lifespan)
        compiled_graph = session.websocket.app.state.compiled_graph
        config = {"configurable": {"thread_id": session_id, "skip_tts": True}}

        graph_input = {"messages": [HumanMessage(content=transcription)]}
        response_text = await _stream_graph_response_to_tts(session, compiled_graph, graph_input, config)

        if response_text is None:
            result = await asyncio.wait_for(
                compiled_graph.ainvoke(
                    graph_input,
                    config=config,
                ),
                timeout=settings.WORKFLOW_TIMEOUT_SECONDS,
            )
            session.workflow_completed_at = time.perf_counter()

            if session.interrupted:
                logger.info("ws_interrupted_after_workflow", session_log_id=session_log_id)
                return

            response_text = sanitize_voice_response(result["messages"][-1].content)
            _record_websocket_response_quality(response_text, session.session_id)

            # Send response text to client
            await session.send_json(MSG_RESPONSE, text=response_text)

            # Step 3: Stream TTS audio phrase-by-phrase
            await _stream_tts_response(session, response_text)

        timings = session.timing_payload()
        await _send_audio_end(session)
        session.is_responding = False

        logger.info(
            "ws_response_complete",
            session_log_id=session_log_id,
            response_length=len(response_text),
            **timings,
        )

    except asyncio.TimeoutError:
        logger.error("ws_workflow_timeout", session_log_id=session_log_id)
        await session.send_json(MSG_ERROR, message="Processing timeout")

    except Exception as e:
        logger.error(
            "ws_processing_error",
            session_log_id=session_log_id,
            error=exception_message_for_log(e),
            exc_info=exc_info_for_log(),
        )
        await session.send_json(MSG_ERROR, message="Processing failed")

    finally:
        session.is_responding = False
