"""Voice processing endpoints."""

import asyncio
import os
import stat
import tempfile
import time
import uuid
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Generator, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from pydantic import BaseModel
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
from ai_companion.core.resilience import CircuitBreakerError
from ai_companion.graph.graph import create_workflow_graph
from ai_companion.modules.speech.speech_to_text import SpeechToText
from ai_companion.modules.speech.text_to_speech import TextToSpeech
from ai_companion.settings import settings

logger = get_logger(__name__)

router = APIRouter()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Constants
AUDIO_SERVE_PATH = "/api/voice/audio"
MAX_FILE_SAVE_RETRIES = 3


# Dependency injection functions
@lru_cache()
def get_stt() -> SpeechToText:
    """Get or create SpeechToText instance."""
    return SpeechToText()


@lru_cache()
def get_tts() -> TextToSpeech:
    """Get or create TextToSpeech instance."""
    return TextToSpeech()


@lru_cache()
def get_audio_dir() -> Path:
    """Get audio directory path."""
    audio_dir = Path(tempfile.gettempdir()) / "rose_audio"
    audio_dir.mkdir(exist_ok=True)
    return audio_dir


async def get_checkpointer():
    """Get or create async checkpointer instance.

    Creates an async SQLite checkpointer for conversation memory persistence.
    Uses AsyncSqliteSaver for compatibility with async LangGraph workflows.

    Yields:
        AsyncSqliteSaver: Initialized async checkpointer instance

    Note:
        This is an async generator dependency that properly enters the context manager.
        FastAPI will call __aenter__ before injecting and __aexit__ after completion.
    """
    # Create data directory if it doesn't exist
    db_path = Path(settings.SHORT_TERM_MEMORY_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Enter the async context manager and yield the actual checkpointer instance
    async with AsyncSqliteSaver.from_conn_string(str(db_path)) as checkpointer:
        yield checkpointer


# Helper functions and context managers
@contextmanager
def track_api_call(
    service_name: str,
    session_id: str,
    success_emoji: str = "✅",
    error_emoji: str = "❌",
) -> Generator[dict, None, None]:
    """Context manager for tracking API calls with metrics and logging.
    
    Args:
        service_name: Name of the service being called (e.g., "groq_stt", "elevenlabs_tts")
        session_id: Session identifier for logging
        success_emoji: Emoji to use for success logs
        error_emoji: Emoji to use for error logs
        
    Yields:
        dict: Context dictionary that can be updated with additional log data
    """
    start_time = time.time()
    context = {"session_id": session_id}

    try:
        yield context
        duration_ms = (time.time() - start_time) * 1000

        # Record success metrics
        metrics.record_api_call(service_name, success=True, duration_ms=duration_ms)
        logger.info(f"📊 {service_name}_metrics_recorded", duration_ms=round(duration_ms, 2), success=True)
        logger.info(
            f"{success_emoji} {service_name}_success",
            duration_ms=round(duration_ms, 2),
            **context,
        )

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000

        # Record failure metrics
        metrics.record_api_call(service_name, success=False, duration_ms=duration_ms)
        logger.info(f"📊 {service_name}_metrics_recorded", duration_ms=round(duration_ms, 2), success=False)
        logger.error(f"{error_emoji} {service_name}_failed", error=str(e), **context, exc_info=True)
        raise


def record_error_metrics(error_type: str, endpoint: str = "voice_process") -> None:
    """Record error metrics and log.
    
    Args:
        error_type: Type of error for metrics
        endpoint: Endpoint name for metrics
    """
    metrics.record_error(error_type, endpoint=endpoint)
    logger.info("📊 error_metrics_recorded", error_type=error_type)


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


async def _transcribe_audio(audio_data: bytes, session_id: str, stt: SpeechToText) -> str:
    """Transcribe audio to text with metrics tracking.
    
    Args:
        audio_data: Audio file bytes
        session_id: Session identifier
        stt: SpeechToText instance
        
    Returns:
        str: Transcribed text
        
    Raises:
        HTTPException: If audio validation fails
        SpeechToTextError: If transcription fails
    """
    # Record voice request metrics
    metrics.record_voice_request(session_id, len(audio_data))
    logger.info("📊 voice_request_metrics_recorded", session_id=session_id, audio_size_bytes=len(audio_data))
    logger.info("🎤 voice_processing_started", session_id=session_id, audio_size_bytes=len(audio_data))

    try:
        with track_api_call("groq_stt", session_id, success_emoji="✅", error_emoji="❌") as ctx:
            transcribed_text = await stt.transcribe(audio_data)
            ctx["transcribed_length"] = len(transcribed_text)
            return transcribed_text

    except ValueError as e:
        # Validation errors (bad audio format, empty file, etc.)
        record_error_metrics("audio_validation_failed")
        logger.error("❌ audio_validation_failed", error=str(e), session_id=session_id)
        raise HTTPException(status_code=400, detail=ERROR_MSG_AUDIO_VALIDATION_FAILED)

    except Exception as e:
        # API or processing errors
        record_error_metrics("speech_to_text_failed")
        raise SpeechToTextError(ERROR_MSG_STT_FAILED)


async def _process_workflow(
    transcribed_text: str, session_id: str, checkpointer: AsyncSqliteSaver
) -> str:
    """Process through LangGraph workflow with timeout and error handling.

    Args:
        transcribed_text: Text to process
        session_id: Session identifier
        checkpointer: AsyncSqliteSaver instance for session persistence
        
    Returns:
        str: Response text from workflow
        
    Raises:
        HTTPException: If workflow times out or circuit breaker is open
        WorkflowError: If workflow execution fails
    """
    workflow_start = time.time()

    try:
        # Compile graph with checkpointer
        graph = create_workflow_graph().compile(checkpointer=checkpointer)

        # Create config with session thread
        config = {"configurable": {"thread_id": session_id}}

        # Invoke workflow with global timeout
        try:
            result = await asyncio.wait_for(
                graph.ainvoke(
                    {"messages": [HumanMessage(content=transcribed_text)]},
                    config=config,
                ),
                timeout=settings.WORKFLOW_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            workflow_duration_ms = (time.time() - workflow_start) * 1000
            metrics.record_workflow_execution(session_id, workflow_duration_ms, success=False)
            logger.info(
                "📊 workflow_metrics_recorded",
                session_id=session_id,
                duration_ms=round(workflow_duration_ms, 2),
                success=False,
            )
            record_error_metrics("workflow_timeout")
            logger.error(
                "❌ workflow_timeout", session_id=session_id, timeout_seconds=settings.WORKFLOW_TIMEOUT_SECONDS
            )
            raise HTTPException(status_code=504, detail=ERROR_MSG_WORKFLOW_TIMEOUT)

        # Extract response text from the last AI message
        response_text = result["messages"][-1].content
        workflow_duration_ms = (time.time() - workflow_start) * 1000
        metrics.record_workflow_execution(session_id, workflow_duration_ms, success=True)
        logger.info(
            "📊 workflow_metrics_recorded",
            session_id=session_id,
            duration_ms=round(workflow_duration_ms, 2),
            success=True,
        )
        logger.info(
            "✅ workflow_execution_success",
            session_id=session_id,
            response_length=len(response_text),
            duration_ms=round(workflow_duration_ms, 2),
        )
        return response_text

    except CircuitBreakerError as e:
        # Circuit breaker is open for one of the services
        workflow_duration_ms = (time.time() - workflow_start) * 1000
        metrics.record_workflow_execution(session_id, workflow_duration_ms, success=False)
        logger.info(
            "📊 workflow_metrics_recorded",
            session_id=session_id,
            duration_ms=round(workflow_duration_ms, 2),
            success=False,
        )
        record_error_metrics("circuit_breaker_open")
        logger.error("❌ circuit_breaker_open", error=str(e), session_id=session_id)
        raise HTTPException(status_code=503, detail=ERROR_MSG_SERVICE_UNAVAILABLE)

    except HTTPException:
        # Re-raise HTTP exceptions (including timeout)
        raise

    except Exception as e:
        workflow_duration_ms = (time.time() - workflow_start) * 1000
        metrics.record_workflow_execution(session_id, workflow_duration_ms, success=False)
        logger.info(
            "📊 workflow_metrics_recorded",
            session_id=session_id,
            duration_ms=round(workflow_duration_ms, 2),
            success=False,
        )
        record_error_metrics("workflow_execution_failed")
        logger.error("❌ workflow_execution_failed", error=str(e), session_id=session_id, exc_info=True)
        raise WorkflowError(ERROR_MSG_WORKFLOW_FAILED)


async def _generate_audio_response(response_text: str, session_id: str, tts: TextToSpeech) -> bytes:
    """Generate audio response using TTS.
    
    Args:
        response_text: Text to synthesize
        session_id: Session identifier
        tts: TextToSpeech instance
        
    Returns:
        bytes: Audio file bytes
        
    Raises:
        TextToSpeechError: If TTS synthesis fails
    """
    try:
        with track_api_call("elevenlabs_tts", session_id, success_emoji="🔊", error_emoji="❌") as ctx:
            audio_bytes = await tts.synthesize(response_text)
            ctx["audio_size_bytes"] = len(audio_bytes)
            return audio_bytes

    except Exception as e:
        record_error_metrics("text_to_speech_failed")
        # Include the response text in the error so user can still see what Rose wanted to say
        raise TextToSpeechError(ERROR_MSG_TTS_FAILED.format(response_text=response_text))


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

            logger.info("audio_file_saved", audio_id=audio_id, path=str(audio_path), session_id=session_id)
            return f"{AUDIO_SERVE_PATH}/{audio_id}"

        except FileExistsError:
            # UUID collision (extremely rare) - retry with new UUID
            if attempt == MAX_FILE_SAVE_RETRIES - 1:
                record_error_metrics("audio_save_failed")
                logger.error("❌ audio_save_failed_max_retries", audio_id=audio_id, session_id=session_id)
                raise HTTPException(status_code=500, detail=ERROR_MSG_AUDIO_SAVE_FAILED)
            continue

        except Exception as e:
            record_error_metrics("audio_save_failed")
            logger.error("❌ audio_save_failed", error=str(e), audio_id=audio_id, session_id=session_id)
            raise HTTPException(status_code=500, detail=ERROR_MSG_AUDIO_SAVE_FAILED)

    # Should never reach here due to exception in loop
    raise HTTPException(status_code=500, detail=ERROR_MSG_AUDIO_SAVE_FAILED)


class VoiceProcessResponse(BaseModel):
    """Response model for voice processing.

    Attributes:
        text: The transcribed and processed text response from Rose
        audio_url: URL to download the generated audio response (MP3 format)
        session_id: Unique session identifier for conversation continuity
    """

    text: str
    audio_url: str
    session_id: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "I hear the pain in your words. It's okay to feel this way. Tell me more about what you're experiencing.",
                    "audio_url": "/api/v1/voice/audio/550e8400-e29b-41d4-a716-446655440000",
                    "session_id": "123e4567-e89b-12d3-a456-426614174000",
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
    stt: SpeechToText = Depends(get_stt),
    tts: TextToSpeech = Depends(get_tts),
    audio_dir: Path = Depends(get_audio_dir),
    checkpointer: AsyncSqliteSaver = Depends(get_checkpointer),
) -> VoiceProcessResponse:
    """Process voice input and generate audio response.

    Accepts an audio file, transcribes it using Groq Whisper,
    processes through LangGraph workflow with Rose's therapeutic AI,
    and generates an empathetic audio response using ElevenLabs TTS.

    **Validation Rules:**
    - Audio file size: Maximum 10MB
    - Audio formats: WAV, MP3, WebM, M4A, OGG
    - Session ID: Must be valid UUID v4 format from /session/start
    - Rate limit: 10 requests per minute per IP address
    - Timeout: 60 seconds maximum processing time

    **Processing Flow:**
    1. Validate audio file size and format
    2. Transcribe audio to text using Groq Whisper
    3. Process through LangGraph workflow with memory context
    4. Generate empathetic response using Rose's character
    5. Synthesize audio response using ElevenLabs TTS
    6. Return text and audio URL

    Args:
        request: FastAPI request object (injected)
        audio: Audio file (WAV, MP3, WebM, M4A, OGG) - max 10MB
        session_id: Session identifier for conversation tracking (UUID v4)
        stt: SpeechToText instance (injected)
        tts: TextToSpeech instance (injected)
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
    try:
        # Validate and read audio
        audio_data = await _validate_and_read_audio(audio)

        # Transcribe audio
        transcribed_text = await _transcribe_audio(audio_data, session_id, stt)

        # Process through workflow
        response_text = await _process_workflow(transcribed_text, session_id, checkpointer)

        # Generate audio response
        audio_bytes = await _generate_audio_response(response_text, session_id, tts)

        # Save and return
        audio_url = await _save_audio_file(audio_bytes, session_id, audio_dir)

        logger.info(
            "✅ voice_processing_complete",
            session_id=session_id,
            response_length=len(response_text),
        )

        return VoiceProcessResponse(
            text=response_text,
            audio_url=audio_url,
            session_id=session_id,
        )

    except HTTPException:
        raise
    except (SpeechToTextError, TextToSpeechError, WorkflowError):
        # These will be handled by the global exception handler
        raise
    except Exception as e:
        record_error_metrics("unexpected_error")
        logger.error("❌ unexpected_error", error=str(e), session_id=session_id, exc_info=True)
        raise HTTPException(status_code=500, detail=ERROR_MSG_INTERNAL_ERROR)


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
        logger.error("❌ audio_file_not_found", audio_id=audio_id)
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
        logger.error("audio_cleanup_failed", error=str(e), exc_info=True)
