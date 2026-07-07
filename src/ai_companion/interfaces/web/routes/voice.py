"""Voice processing endpoints.

This module provides the core voice processing API for Rose, including:
- Audio upload and validation
- Speech-to-text transcription
- LangGraph workflow processing
- Text-to-speech synthesis
- Comprehensive latency instrumentation for performance analysis

Reference: docs/PERFORMANCE_BACKLOG.md, docs/ARCHITECTURE.md
"""

import asyncio
import base64
import os
import stat
import tempfile
import time
import uuid
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import AsyncGenerator, Generator, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from ai_companion.config.server_config import (
    AUDIO_CLEANUP_MAX_AGE_HOURS,
    ERROR_MSG_AUDIO_EMPTY,
    ERROR_MSG_AUDIO_NOT_FOUND,
    ERROR_MSG_AUDIO_SAVE_FAILED,
    ERROR_MSG_AUDIO_TOO_LARGE,
    ERROR_MSG_AUDIO_VALIDATION_FAILED,
    ERROR_MSG_INTERNAL_ERROR,
    ERROR_MSG_SERVICE_UNAVAILABLE,
    ERROR_MSG_STT_FAILED,
    ERROR_MSG_TTS_FAILED,
    ERROR_MSG_WORKFLOW_FAILED,
    ERROR_MSG_WORKFLOW_TIMEOUT,
    MAX_AUDIO_FILE_SIZE_BYTES,
    SECONDS_PER_HOUR,
)
from ai_companion.core.exceptions import SpeechToTextError, TextToSpeechError, WorkflowError
from ai_companion.core.logging_config import get_logger
from ai_companion.core.metrics import metrics, track_performance
from ai_companion.core.privacy_logging import (
    exc_info_for_log,
    exception_message_for_log,
    sensitive_text_for_log,
    session_id_for_log,
)
from ai_companion.core.resilience import CircuitBreakerError
from ai_companion.graph.utils.helpers import get_text_to_speech_module
from ai_companion.modules.speech.stt_provider import STTProvider, get_stt_provider
from ai_companion.modules.speech.tts_provider import TTSProvider
from ai_companion.settings import settings

logger = get_logger(__name__)

router = APIRouter()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Constants - No Magic Numbers (Uncle Bob approved)
AUDIO_SERVE_PATH = "/api/v1/voice/audio"
MAX_FILE_SAVE_RETRIES = 3
MS_PER_SECOND = 1000  # Conversion factor for timing calculations

# Silence handling: varied responses to avoid repetitive "I'm here" messages
SILENCE_RESPONSES = [
    "I'm here whenever you're ready.",
    "Take your time. I'm not going anywhere.",
    "No rush at all.",
]
MAX_SILENCE_RESPONSES = len(SILENCE_RESPONSES)

# Per-session silence counters: {session_id: count}
_silence_counts: dict[str, int] = {}


@dataclass
class PipelineTimings:
    """Tracks latency for each stage of the voice processing pipeline.

    All timings are in milliseconds. This enables identification of
    bottlenecks and measurement of optimization impact.

    Reference: docs/PERFORMANCE_BACKLOG.md
    """

    audio_validation_ms: float = 0.0
    stt_ms: float = 0.0
    workflow_ms: float = 0.0
    tts_ms: float = 0.0
    audio_save_ms: float = 0.0
    total_ms: float = 0.0

    # Workflow sub-stages (when available from graph execution)
    memory_retrieval_ms: float = 0.0
    llm_generation_ms: float = 0.0
    memory_extraction_ms: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "audio_validation_ms": round(self.audio_validation_ms, 2),
            "stt_ms": round(self.stt_ms, 2),
            "workflow_ms": round(self.workflow_ms, 2),
            "tts_ms": round(self.tts_ms, 2),
            "audio_save_ms": round(self.audio_save_ms, 2),
            "total_ms": round(self.total_ms, 2),
            "memory_retrieval_ms": round(self.memory_retrieval_ms, 2),
            "llm_generation_ms": round(self.llm_generation_ms, 2),
            "memory_extraction_ms": round(self.memory_extraction_ms, 2),
        }

    def log_summary(self, session_id: str) -> None:
        """Log a formatted summary of pipeline timings."""
        logger.info("pipeline_timings", session_log_id=session_id_for_log(session_id), **self.to_dict())


@asynccontextmanager
async def timed_stage(timings: PipelineTimings, stage_name: str) -> AsyncGenerator[None, None]:
    """Context manager to time a pipeline stage.

    Args:
        timings: PipelineTimings instance to update
        stage_name: Name of the stage (must match a PipelineTimings attribute)

    Example:
        async with timed_stage(timings, "stt_ms"):
            result = await stt.transcribe(audio_data)
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * MS_PER_SECOND
        setattr(timings, stage_name, duration_ms)


# Dependency injection functions
@lru_cache()
def get_stt() -> STTProvider:
    """Get or create configured speech-to-text provider."""
    return get_stt_provider()


def get_tts() -> TTSProvider:
    """Get the shared text-to-speech provider singleton.

    Delegates to get_text_to_speech_module() so that the TTS cache warmed
    on startup (app.py lifespan) is reused by all voice routes and the
    WebSocket path rather than being silently discarded.
    """
    return get_text_to_speech_module()


@lru_cache()
def get_audio_dir() -> Path:
    """Get audio directory path."""
    audio_dir = Path(tempfile.gettempdir()) / "rose_audio"
    audio_dir.mkdir(exist_ok=True)
    return audio_dir


# Module-level constant for backwards compatibility with tests
# Tests import this directly, so we need to provide it
AUDIO_DIR = get_audio_dir()


def get_compiled_graph(request: Request):
    """Get the pre-compiled graph from app state.

    The graph and checkpointer are initialized once during app lifespan
    (see app.py) and shared across all requests.
    """
    return request.app.state.compiled_graph


# Helper functions and context managers
@contextmanager
def track_api_call(
    service_name: str,
    session_id: str,
    success_marker: str = "success",
    error_marker: str = "error",
) -> Generator[dict, None, None]:
    """Context manager for tracking API calls with metrics and logging.

    Args:
        service_name: Name of the service being called (e.g., "groq_stt", "elevenlabs_tts")
        session_id: Session identifier for logging
        success_marker: Plain-text marker for success logs
        error_marker: Plain-text marker for error logs

    Yields:
        dict: Context dictionary that can be updated with additional log data
    """
    start_time = time.time()
    session_log_id = session_id_for_log(session_id)
    context = {"session_log_id": session_log_id}

    try:
        yield context
        duration_ms = (time.time() - start_time) * 1000

        # Record success metrics
        metrics.record_api_call(service_name, success=True, duration_ms=duration_ms)
        logger.info("metrics_recorded", service=service_name, duration_ms=round(duration_ms, 2), success=True)
        logger.info(
            "service_success",
            service=service_name,
            marker=success_marker,
            duration_ms=round(duration_ms, 2),
            **context,
        )

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000

        # Record failure metrics
        metrics.record_api_call(service_name, success=False, duration_ms=duration_ms)
        logger.info("metrics_recorded", service=service_name, duration_ms=round(duration_ms, 2), success=False)
        logger.error(
            "service_failed",
            service=service_name,
            marker=error_marker,
            error=exception_message_for_log(e),
            **context,
            exc_info=exc_info_for_log(),
        )
        raise


def record_error_metrics(error_type: str, endpoint: str = "voice_process") -> None:
    """Record error metrics and log.

    Args:
        error_type: Type of error for metrics
        endpoint: Endpoint name for metrics
    """
    metrics.record_error(error_type, endpoint=endpoint)
    logger.info("error_metrics_recorded", error_type=error_type)


async def _validate_and_read_audio(audio: UploadFile) -> bytes:
    """Validate and read audio file.

    Args:
        audio: Uploaded audio file

    Returns:
        bytes: Audio file content

    Raises:
        HTTPException: If audio is invalid or too large
    """
    audio_data = await audio.read()

    # Validate audio size
    if len(audio_data) > MAX_AUDIO_FILE_SIZE_BYTES:
        record_error_metrics("audio_too_large")
        raise HTTPException(status_code=413, detail=ERROR_MSG_AUDIO_TOO_LARGE)

    if not audio_data:
        record_error_metrics("audio_empty")
        raise HTTPException(status_code=400, detail=ERROR_MSG_AUDIO_EMPTY)

    return audio_data


async def _transcribe_audio(audio_data: bytes, session_id: str, stt: STTProvider) -> str:
    """Transcribe audio to text with metrics tracking.

    Args:
        audio_data: Audio file bytes
        session_id: Session identifier
        stt: Speech-to-text provider

    Returns:
        str: Transcribed text

    Raises:
        HTTPException: If audio validation fails
        SpeechToTextError: If transcription fails
    """
    session_log_id = session_id_for_log(session_id)

    # Record voice request metrics
    metrics.record_voice_request(session_id, len(audio_data))
    logger.info("voice_request_metrics_recorded", session_log_id=session_log_id, audio_size_bytes=len(audio_data))
    logger.info("voice_processing_started", session_log_id=session_log_id, audio_size_bytes=len(audio_data))

    try:
        with track_api_call(stt.name, session_id) as ctx:
            transcribed_text = await stt.transcribe(audio_data)
            ctx["transcribed_length"] = len(transcribed_text)

            # Log transcription for debugging without raw text by default.
            logger.info(
                "transcription_complete",
                session_log_id=session_log_id,
                text_length=len(transcribed_text),
                text=sensitive_text_for_log(transcribed_text),
            )

            # Input guard: filter out known Whisper hallucination artifacts.
            # Only exact matches - substring matching caused false positives
            # (e.g. "thank you" is legitimate user speech, "audio" appears in real sentences)
            whisper_artifacts = {"subtitles by", "copyright", "thanks for watching"}
            cleaned = transcribed_text.strip().lower()

            if not cleaned or cleaned in whisper_artifacts:
                logger.warning(
                    "input_guard_filtered",
                    reason="whisper_artifact",
                    text_length=len(transcribed_text),
                    text=sensitive_text_for_log(transcribed_text),
                    session_log_id=session_log_id,
                )
                return ""

            return transcribed_text

    except ValueError as e:
        # Validation errors (bad audio format, empty file, etc.)
        record_error_metrics("audio_validation_failed")
        logger.error("audio_validation_failed", error=exception_message_for_log(e), session_log_id=session_log_id)
        raise HTTPException(status_code=400, detail=ERROR_MSG_AUDIO_VALIDATION_FAILED)

    except Exception:
        # API or processing errors
        record_error_metrics("speech_to_text_failed")
        raise SpeechToTextError(ERROR_MSG_STT_FAILED)


async def _process_workflow(transcribed_text: str, session_id: str, compiled_graph) -> tuple[str, Optional[bytes]]:
    """Process through LangGraph workflow with timeout and error handling.

    Args:
        transcribed_text: Text to process
        session_id: Session identifier
        compiled_graph: Pre-compiled LangGraph workflow from app state

    Returns:
        tuple[str, Optional[bytes]]: Response text and optional audio buffer from workflow

    Raises:
        HTTPException: If workflow times out or circuit breaker is open
        WorkflowError: If workflow execution fails
    """
    session_log_id = session_id_for_log(session_id)
    workflow_start = time.time()

    try:
        # Create config with session thread
        config = {"configurable": {"thread_id": session_id}}

        # Invoke workflow with global timeout
        try:
            result = await asyncio.wait_for(
                compiled_graph.ainvoke(
                    {"messages": [HumanMessage(content=transcribed_text)]},
                    config=config,
                ),
                timeout=settings.WORKFLOW_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            workflow_duration_ms = (time.time() - workflow_start) * 1000
            metrics.record_workflow_execution(session_id, workflow_duration_ms, success=False)
            logger.info(
                "workflow_metrics_recorded",
                session_log_id=session_log_id,
                duration_ms=round(workflow_duration_ms, 2),
                success=False,
            )
            record_error_metrics("workflow_timeout")
            logger.error(
                "workflow_timeout", session_log_id=session_log_id, timeout_seconds=settings.WORKFLOW_TIMEOUT_SECONDS
            )
            raise HTTPException(status_code=504, detail=ERROR_MSG_WORKFLOW_TIMEOUT)

        # Extract response text from the last AI message
        response_text = result["messages"][-1].content
        audio_buffer = result.get("audio_buffer")
        workflow_duration_ms = (time.time() - workflow_start) * 1000
        metrics.record_workflow_execution(session_id, workflow_duration_ms, success=True)
        logger.info(
            "workflow_metrics_recorded",
            session_log_id=session_log_id,
            duration_ms=round(workflow_duration_ms, 2),
            success=True,
        )
        logger.info(
            "workflow_execution_success",
            session_log_id=session_log_id,
            response_length=len(response_text),
            duration_ms=round(workflow_duration_ms, 2),
        )
        return response_text, audio_buffer

    except CircuitBreakerError as e:
        # Circuit breaker is open for one of the services
        workflow_duration_ms = (time.time() - workflow_start) * 1000
        metrics.record_workflow_execution(session_id, workflow_duration_ms, success=False)
        logger.info(
            "workflow_metrics_recorded",
            session_log_id=session_log_id,
            duration_ms=round(workflow_duration_ms, 2),
            success=False,
        )
        record_error_metrics("circuit_breaker_open")
        logger.error("circuit_breaker_open", error=exception_message_for_log(e), session_log_id=session_log_id)
        raise HTTPException(status_code=503, detail=ERROR_MSG_SERVICE_UNAVAILABLE)

    except HTTPException:
        # Re-raise HTTP exceptions (including timeout)
        raise

    except Exception as e:
        workflow_duration_ms = (time.time() - workflow_start) * 1000
        metrics.record_workflow_execution(session_id, workflow_duration_ms, success=False)
        logger.info(
            "workflow_metrics_recorded",
            session_log_id=session_log_id,
            duration_ms=round(workflow_duration_ms, 2),
            success=False,
        )
        record_error_metrics("workflow_execution_failed")
        logger.error(
            "workflow_execution_failed",
            error=exception_message_for_log(e),
            session_log_id=session_log_id,
            input_text=sensitive_text_for_log(transcribed_text, max_chars=200),
            input_text_length=len(transcribed_text),
            exc_info=exc_info_for_log(),
        )
        # Raise a WorkflowError with a concise message while logging the full stack trace
        raise WorkflowError(f"{ERROR_MSG_WORKFLOW_FAILED} (type={type(e).__name__})")


async def _generate_audio_response(response_text: str, session_id: str, tts: TTSProvider) -> bytes:
    """Generate audio response using TTS.

    Args:
        response_text: Text to synthesize
        session_id: Session identifier
        tts: Configured text-to-speech provider

    Returns:
        bytes: Audio file bytes

    Raises:
        TextToSpeechError: If TTS synthesis fails
    """
    try:
        with track_api_call(tts.name, session_id, success_marker="audio_success") as ctx:
            audio_bytes = await tts.synthesize_cached(response_text)
            ctx["audio_size_bytes"] = len(audio_bytes)
            return audio_bytes

    except Exception:
        record_error_metrics("text_to_speech_failed")
        raise TextToSpeechError(ERROR_MSG_TTS_FAILED)


async def _save_audio_file(audio_bytes: bytes, session_id: str, audio_dir: Path) -> str:
    """Save audio file with secure permissions and retry logic.

    Args:
        audio_bytes: Audio file bytes
        session_id: Session identifier for logging
        audio_dir: Directory to save audio files

    Returns:
        str: Audio URL path

    Raises:
        HTTPException: If file save fails after retries
    """
    session_log_id = session_id_for_log(session_id)

    for attempt in range(MAX_FILE_SAVE_RETRIES):
        audio_id = str(uuid.uuid4())
        audio_path = audio_dir / f"{audio_id}.mp3"

        try:
            # Create file with secure permissions (owner read/write only)
            fd = os.open(str(audio_path), os.O_CREAT | os.O_WRONLY | os.O_EXCL, stat.S_IRUSR | stat.S_IWUSR)
            try:
                os.write(fd, audio_bytes)
            finally:
                os.close(fd)

            logger.info("audio_file_saved", audio_id=audio_id, session_log_id=session_log_id)
            return f"{AUDIO_SERVE_PATH}/{audio_id}"

        except FileExistsError:
            # UUID collision (extremely rare) - retry with new UUID
            if attempt == MAX_FILE_SAVE_RETRIES - 1:
                record_error_metrics("audio_save_failed")
                logger.error("audio_save_failed_max_retries", audio_id=audio_id, session_log_id=session_log_id)
                raise HTTPException(status_code=500, detail=ERROR_MSG_AUDIO_SAVE_FAILED)
            continue

        except Exception as e:
            record_error_metrics("audio_save_failed")
            logger.error(
                "audio_save_failed",
                error=exception_message_for_log(e),
                audio_id=audio_id,
                session_log_id=session_log_id,
            )
            raise HTTPException(status_code=500, detail=ERROR_MSG_AUDIO_SAVE_FAILED)

    # Should never reach here due to exception in loop
    raise HTTPException(status_code=500, detail=ERROR_MSG_AUDIO_SAVE_FAILED)


class PipelineTimingsResponse(BaseModel):
    """Response model for pipeline timing metrics.

    All values are in milliseconds.
    """

    audio_validation_ms: float = Field(default=0.0, description="Time to validate audio input")
    stt_ms: float = Field(default=0.0, description="Speech-to-text transcription time")
    workflow_ms: float = Field(default=0.0, description="LangGraph workflow execution time")
    tts_ms: float = Field(default=0.0, description="Text-to-speech synthesis time")
    audio_save_ms: float = Field(default=0.0, description="Time to save audio file")
    total_ms: float = Field(default=0.0, description="Total end-to-end processing time")
    memory_retrieval_ms: float = Field(default=0.0, description="Long-term memory retrieval time")
    llm_generation_ms: float = Field(default=0.0, description="LLM response generation time")
    memory_extraction_ms: float = Field(default=0.0, description="Memory extraction time")


class VoiceProcessResponse(BaseModel):
    """Response model for voice processing.

    Attributes:
        text: The processed text response from Rose
        user_text: The user's own transcribed speech (for UI display)
        audio_url: URL to download the generated audio response (MP3 format)
        session_id: Unique session identifier for conversation continuity
        timings: Optional pipeline timing metrics for performance analysis
    """

    text: str
    user_text: str = ""
    audio_url: str
    audio_data: Optional[str] = Field(
        default=None, description="Base64-encoded MP3 audio (inline delivery, avoids extra HTTP round-trip)"
    )
    session_id: str
    timings: Optional[PipelineTimingsResponse] = Field(
        default=None, description="Pipeline latency breakdown (only included when FEATURE_TIMING_METRICS is enabled)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "That sounds heavy. Take one slow breath with me, then tell me what part feels loudest right now.",
                    "audio_url": "/api/v1/voice/audio/550e8400-e29b-41d4-a716-446655440000",
                    "session_id": "123e4567-e89b-12d3-a456-426614174000",
                    "timings": {
                        "audio_validation_ms": 12.5,
                        "stt_ms": 850.3,
                        "workflow_ms": 1200.0,
                        "tts_ms": 980.2,
                        "audio_save_ms": 15.8,
                        "total_ms": 3058.8,
                        "memory_retrieval_ms": 150.0,
                        "llm_generation_ms": 800.0,
                        "memory_extraction_ms": 100.0,
                    },
                }
            ]
        }
    }


@router.post("/voice/process", response_model=VoiceProcessResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
@track_performance("voice_processing")
async def process_voice(
    request: Request,
    audio: UploadFile = File(..., description="Audio file containing user's voice input"),
    session_id: str = Form(..., description="UUID v4 session identifier from /session/start"),
    stt: STTProvider = Depends(get_stt),
    tts: TTSProvider = Depends(get_tts),
    audio_dir: Path = Depends(get_audio_dir),
    compiled_graph=Depends(get_compiled_graph),
) -> VoiceProcessResponse:
    """Process voice input and generate audio response.

    Accepts an audio file, transcribes it using the configured STT provider,
    processes through the LangGraph workflow with safety and memory controls,
    and generates a short voice-native emotional-support response.

    **Validation Rules:**
    - Audio file size: Maximum 10MB
    - Audio formats: WAV, MP3, WebM, M4A, OGG
    - Session ID: Must be valid UUID v4 format from /session/start
    - Rate limit: 10 requests per minute per IP address
    - Timeout: 60 seconds maximum processing time

    **Processing Flow:**
    1. Validate audio file size and format
    2. Transcribe audio to text using the configured STT provider
    3. Process through LangGraph workflow with safety and memory context
    4. Generate a short, voice-native emotional-support response
    5. Synthesize audio response using the configured TTS provider
    6. Return text and audio URL

    Args:
        request: FastAPI request object (injected)
        audio: Audio file (WAV, MP3, WebM, M4A, OGG) - max 10MB
        session_id: Session identifier for conversation tracking (UUID v4)
        stt: Speech-to-text provider (injected)
        tts: Text-to-speech provider (injected)
        audio_dir: Audio directory path (injected)
        checkpointer: AsyncSqliteSaver instance (injected)

    Returns:
        VoiceProcessResponse: Contains response text, audio URL, and session ID

    Raises:
        HTTPException 400: Invalid audio format, empty file, or validation error
        HTTPException 413: Audio file exceeds 10MB size limit
        HTTPException 429: Rate limit exceeded (10 requests/minute)
        HTTPException 503: External service unavailable (Groq, ElevenLabs, Qdrant)
        HTTPException 504: Processing timeout (>60 seconds)
        HTTPException 500: Internal server error
    """
    # Initialize timing instrumentation
    timings = PipelineTimings()
    pipeline_start = time.perf_counter()
    session_log_id = session_id_for_log(session_id)

    try:
        # Stage 1: Validate and read audio
        async with timed_stage(timings, "audio_validation_ms"):
            audio_data = await _validate_and_read_audio(audio)

        # Stage 2: Transcribe audio (Speech-to-Text)
        async with timed_stage(timings, "stt_ms"):
            transcribed_text = await _transcribe_audio(audio_data, session_id, stt)

        # Input guard: handle silence with varied responses.
        if not transcribed_text:
            count = _silence_counts.get(session_id, 0)
            _silence_counts[session_id] = count + 1
            logger.info("silence_detected", session_log_id=session_log_id, silence_count=count + 1)

            # After exhausting varied responses, return empty to avoid spamming
            if count >= MAX_SILENCE_RESPONSES:
                return VoiceProcessResponse(text="", user_text="", audio_url="", session_id=session_id)

            silence_text = SILENCE_RESPONSES[count]
            try:
                audio_bytes = await _generate_audio_response(silence_text, session_id, tts)
                audio_url = await _save_audio_file(audio_bytes, session_id, audio_dir)
            except Exception:
                logger.warning("silence_tts_fallback", session_log_id=session_log_id)
                return VoiceProcessResponse(
                    text=silence_text, user_text=transcribed_text, audio_url="", session_id=session_id
                )
            return VoiceProcessResponse(
                text=silence_text, user_text=transcribed_text, audio_url=audio_url, session_id=session_id
            )

        # User spoke - reset silence counter for this session
        _silence_counts.pop(session_id, None)

        # Stage 3: Process through LangGraph workflow
        async with timed_stage(timings, "workflow_ms"):
            response_text, workflow_audio = await _process_workflow(transcribed_text, session_id, compiled_graph)

        # Stage 4: Generate audio response (Text-to-Speech)
        audio_bytes: bytes | None = None
        async with timed_stage(timings, "tts_ms"):
            if workflow_audio:
                audio_bytes = workflow_audio
                logger.info("using_workflow_generated_audio", session_log_id=session_log_id)
            else:
                try:
                    audio_bytes = await _generate_audio_response(response_text, session_id, tts)
                except TextToSpeechError:
                    metrics.increment_counter("voice_tts_text_only_fallback_total", tags={"tts_provider": tts.name})
                    logger.warning(
                        "voice_tts_text_only_fallback",
                        session_log_id=session_log_id,
                        tts_provider=tts.name,
                    )

        # Stage 5: Save audio file
        audio_url = ""
        if audio_bytes:
            async with timed_stage(timings, "audio_save_ms"):
                audio_url = await _save_audio_file(audio_bytes, session_id, audio_dir)

        # Calculate total time
        timings.total_ms = (time.perf_counter() - pipeline_start) * MS_PER_SECOND

        # Log timing summary
        timings.log_summary(session_id)

        # Record histogram metrics for monitoring
        metrics.record_histogram("pipeline_total_ms", timings.total_ms)
        metrics.record_histogram("pipeline_stt_ms", timings.stt_ms)
        metrics.record_histogram("pipeline_workflow_ms", timings.workflow_ms)
        metrics.record_histogram("pipeline_tts_ms", timings.tts_ms)

        logger.info(
            "voice_processing_complete",
            session_log_id=session_log_id,
            response_length=len(response_text),
            total_ms=round(timings.total_ms, 2),
        )

        # Build response with optional timing metrics
        audio_data_b64 = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None
        response = VoiceProcessResponse(
            text=response_text,
            user_text=transcribed_text,
            audio_url=audio_url,
            audio_data=audio_data_b64,
            session_id=session_id,
        )

        # Include timing metrics if feature flag is enabled
        if settings.FEATURE_TIMING_METRICS_ENABLED:
            response.timings = PipelineTimingsResponse(**timings.to_dict())

        return response

    except HTTPException:
        raise
    except SpeechToTextError as e:
        logger.error(
            "speech_to_text_error",
            session_log_id=session_log_id,
            error=exception_message_for_log(e),
            exc_info=exc_info_for_log(),
        )
        raise
    except TextToSpeechError as e:
        logger.error(
            "text_to_speech_error",
            session_log_id=session_log_id,
            error=exception_message_for_log(e),
            exc_info=exc_info_for_log(),
        )
        raise
    except WorkflowError as e:
        # Log extra details for workflow failures to help debugging
        logger.error(
            "workflow_error",
            session_log_id=session_log_id,
            error=exception_message_for_log(e),
            exc_info=exc_info_for_log(),
        )
        record_error_metrics("workflow_execution_failed")
        raise
    except Exception as e:
        record_error_metrics("unexpected_error")
        logger.error(
            "unexpected_error",
            error=exception_message_for_log(e),
            session_log_id=session_log_id,
            exc_info=exc_info_for_log(),
        )
        raise HTTPException(status_code=500, detail=ERROR_MSG_INTERNAL_ERROR)


@router.post("/voice/stream-tts")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
@track_performance("voice_stream_tts")
async def stream_tts(
    request: Request,
    text: str = Form(..., description="Text to synthesize"),
    session_id: str = Form(..., description="Session ID for logging"),
    tts: TTSProvider = Depends(get_tts),
) -> StreamingResponse:
    """Stream TTS audio directly to the client.

    Phase 2 Optimization: This endpoint streams audio chunks as they are
    generated by ElevenLabs, reducing time-to-first-audio by 200-500ms.

    The client receives audio chunks as they become available, enabling
    playback to start before the full audio is synthesized.

    **Use Cases:**
    - Real-time voice response without waiting for full synthesis
    - Lower perceived latency for end users
    - Better UX for longer responses

    Args:
        request: FastAPI request object (injected)
        text: Text to synthesize to speech
        session_id: Session identifier for logging
        tts: Text-to-speech provider (injected)

    Returns:
        StreamingResponse: MP3 audio stream with chunked transfer encoding
    """
    session_log_id = session_id_for_log(session_id)
    logger.info("stream_tts_started", session_log_id=session_log_id, text_length=len(text))

    async def audio_stream_generator():
        """Generate audio chunks from TTS streaming."""
        try:
            async for chunk in tts.synthesize_streaming(text):
                yield chunk
        except Exception as e:
            logger.error("stream_tts_error", session_log_id=session_log_id, error=exception_message_for_log(e))
            # Stream ends on error - client will handle incomplete audio

    return StreamingResponse(
        audio_stream_generator(),
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "no-cache",
            "Transfer-Encoding": "chunked",
        },
    )


@router.get("/voice/audio/{audio_id}")
@track_performance("audio_serving")
async def get_audio(audio_id: str, audio_dir: Path = Depends(get_audio_dir)) -> FileResponse:
    """Serve generated audio file.

    Retrieves a previously generated audio response file by its unique identifier.
    Audio files are automatically cleaned up after 24 hours.

    **Validation Rules:**
    - Audio ID: Must be valid UUID v4 format
    - File retention: Audio files are deleted after 24 hours
    - Format: MP3 audio file
    - Cache: No caching (Cache-Control: no-cache)

    Args:
        audio_id: Unique identifier for the audio file (UUID v4)
        audio_dir: Audio directory path (injected)

    Returns:
        FileResponse: MP3 audio file as streaming response

    Raises:
        HTTPException 404: Audio file not found or expired
    """
    audio_path = audio_dir / f"{audio_id}.mp3"

    if not audio_path.exists():
        record_error_metrics("audio_not_found", endpoint="audio_serving")
        logger.error("audio_file_not_found", audio_id=audio_id)
        raise HTTPException(status_code=404, detail=ERROR_MSG_AUDIO_NOT_FOUND)

    logger.info("audio_file_served", audio_id=audio_id)

    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        headers={"Cache-Control": "no-cache"},
    )


async def cleanup_old_audio_files(max_age_hours: Optional[int] = None, audio_dir: Optional[Path] = None) -> None:
    """Clean up audio files older than specified hours (async version).

    Args:
        max_age_hours: Maximum age of files to keep in hours (defaults to AUDIO_CLEANUP_MAX_AGE_HOURS)
        audio_dir: Audio directory path (defaults to get_audio_dir())
    """
    try:
        if audio_dir is None:
            audio_dir = get_audio_dir()

        max_age = max_age_hours if max_age_hours is not None else AUDIO_CLEANUP_MAX_AGE_HOURS
        current_time = time.time()
        max_age_seconds = max_age * SECONDS_PER_HOUR
        deleted_count = 0

        for audio_file in audio_dir.glob("*.mp3"):
            file_age = current_time - audio_file.stat().st_mtime
            if file_age > max_age_seconds:
                # Use asyncio for file operations to avoid blocking
                await asyncio.to_thread(audio_file.unlink)
                deleted_count += 1
                logger.info("audio_file_deleted", filename=audio_file.name, age_hours=file_age / SECONDS_PER_HOUR)

        logger.info("audio_cleanup_complete", deleted_count=deleted_count, max_age_hours=max_age)

    except Exception as e:
        logger.error("audio_cleanup_failed", error=exception_message_for_log(e), exc_info=exc_info_for_log())
